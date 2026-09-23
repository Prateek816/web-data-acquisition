"""Deterministic extraction: parsed structured records -> Claim / Contact candidates.

- No network, no DB, no LLM. Takes a parsed record in, returns candidates out.
- Confidence is a FIXED value per field type (never learned / LLM-estimated).
- Values are source values, stripped only (status fields lowercased). Semantic
  normalization (names, phones, addresses, domains) happens downstream in
  normalize/*, so this module does not import it.
- Candidates carry no entity_id; entities/resolver.py attaches it.
- Records may be dataclasses/objects (attribute access) or plain dicts.

Field names follow the canonical data model (`cslb_license_status`, ...). Edit
the FieldSpec tables below if the team standardizes different names.
NOTE: the CSLB field list comes from the planning docs, not an inspected real
export. Verify against a real file (execution plan Part 20, step 2).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Optional

log = logging.getLogger(__name__)

OBSERVED = "observed"
INFERRED = "inferred"

CSLB_EXTRACTOR_VERSION = "cslb_extractor_v1"
SOS_EXTRACTOR_VERSION = "ca_sos_extractor_v1"
SITE_CONTACT_EXTRACTOR_VERSION = "company_site_contact_v1"

# Starting TTLs (days). PROPOSED, unmeasured. Callers should pass overrides from
# config/source_policies.py via `ttl_days` (keyed by claim field or ttl group).
DEFAULT_TTL_DAYS: dict[str, int] = {"cslb": 30, "ca_sos": 90, "company_site": 30}


@dataclass(frozen=True)
class ClaimCandidate:
    """A Claim before persistence. claim_store.save_claim enforces completeness."""
    field: str
    value: Any
    observed_or_inferred: str
    confidence: float
    valid_from: datetime
    observed_at: datetime
    expires_at: datetime
    source_snapshot_id: str
    extractor_version: str
    entity_id: Optional[str] = None


@dataclass(frozen=True)
class ContactCandidate:
    channel: str                         # phone | email | website
    value: str                           # raw; coordinator normalizes via normalize_contact_value
    source: str
    source_snapshot_id: str
    observed_at: datetime
    # Discovery never verifies (verification is the main system's job).
    verification_state: str = field(default="unverified", init=False)


@dataclass
class ExtractionResult:
    claims: list[ClaimCandidate] = field(default_factory=list)
    contacts: list[ContactCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class FieldSpec:
    claim_field: str
    attr: str
    confidence: float
    ttl_group: str
    lower: bool = False


CSLB_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("cslb_license_number", "license_number", 0.99, "cslb"),
    FieldSpec("cslb_business_name", "business_name", 0.95, "cslb"),
    FieldSpec("cslb_classification", "classification", 0.95, "cslb"),
    FieldSpec("cslb_license_status", "status", 0.95, "cslb", lower=True),
    FieldSpec("cslb_address", "address", 0.90, "cslb"),
    FieldSpec("cslb_county", "county", 0.95, "cslb"),
    FieldSpec("cslb_phone", "phone", 0.90, "cslb"),
    FieldSpec("cslb_bond_info", "bond_info", 0.90, "cslb"),
    FieldSpec("cslb_workers_comp", "wc_info", 0.90, "cslb"),
    # Optional: only emitted if the parser exposes them (planning docs mention them).
    FieldSpec("cslb_issue_date", "issue_date", 0.95, "cslb"),
    FieldSpec("cslb_expiry_date", "expiry_date", 0.95, "cslb"),
)

SOS_FIELDS: tuple[FieldSpec, ...] = (
    FieldSpec("sos_legal_name", "legal_name", 0.95, "ca_sos"),
    FieldSpec("sos_entity_number", "entity_number", 0.99, "ca_sos"),
    FieldSpec("sos_entity_status", "status", 0.95, "ca_sos", lower=True),
    FieldSpec("sos_formation_date", "formation_date", 0.95, "ca_sos"),
    FieldSpec("sos_registered_agent", "registered_agent", 0.90, "ca_sos"),
    FieldSpec("sos_address", "address", 0.90, "ca_sos"),
    FieldSpec("sos_filing_history", "filing_history", 0.90, "ca_sos"),
)

# Regex-derived contact facts are less certain than structured fields.
SITE_CONTACT_CONFIDENCE = 0.80


# ---------------------------------------------------------------- helpers

def _utc(dt: Optional[datetime]) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def _read(record: Any, name: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(name)
    return getattr(record, name, None)


def _clean(value: Any, lower: bool = False) -> Any:
    """Strip strings, drop blanks, JSON-friendly dates; None means 'no claim'."""
    if value is None:
        return None
    if isinstance(value, str):
        v = " ".join(value.split())
        if not v:
            return None
        return v.lower() if lower else v
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        items = [_clean(x) for x in value]
        items = [x for x in items if x is not None]
        return items or None
    return value


def _ttl(ttl_days: Optional[Mapping[str, int]], claim_field: str, group: str) -> int:
    merged = {**DEFAULT_TTL_DAYS, **(ttl_days or {})}
    return int(merged.get(claim_field, merged[group]))


def _require_snapshot(source_snapshot_id: str) -> None:
    if not source_snapshot_id:
        raise ValueError("source_snapshot_id is required: no claim may exist without provenance")


def _claims_from_specs(
    record: Any,
    specs: Iterable[FieldSpec],
    *,
    source_snapshot_id: str,
    observed_at: datetime,
    ttl_days: Optional[Mapping[str, int]],
    extractor_version: str,
) -> list[ClaimCandidate]:
    claims: list[ClaimCandidate] = []
    for spec in specs:
        value = _clean(_read(record, spec.attr), lower=spec.lower)
        if value is None:
            continue                      # absent/blank field -> no claim (never a null claim)
        claims.append(ClaimCandidate(
            field=spec.claim_field,
            value=value,
            observed_or_inferred=OBSERVED,
            confidence=spec.confidence,
            valid_from=observed_at,
            observed_at=observed_at,
            expires_at=observed_at + timedelta(days=_ttl(ttl_days, spec.claim_field, spec.ttl_group)),
            source_snapshot_id=source_snapshot_id,
            extractor_version=extractor_version,
        ))
    return claims


# ---------------------------------------------------------------- CSLB

def extract_cslb(
    record: Any,
    *,
    source_snapshot_id: str,
    observed_at: Optional[datetime] = None,
    ttl_days: Optional[Mapping[str, int]] = None,
) -> ExtractionResult:
    """ParsedCSLBRecord -> claims (+ phone contact)."""
    _require_snapshot(source_snapshot_id)
    ts = _utc(observed_at)
    result = ExtractionResult(claims=_claims_from_specs(
        record, CSLB_FIELDS, source_snapshot_id=source_snapshot_id, observed_at=ts,
        ttl_days=ttl_days, extractor_version=CSLB_EXTRACTOR_VERSION,
    ))
    phone = _clean(_read(record, "phone"))
    if phone:
        result.contacts.append(ContactCandidate("phone", phone, "cslb", source_snapshot_id, ts))
    return result


# ---------------------------------------------------------------- CA SOS

def extract_sos(
    record: Any,
    *,
    source_snapshot_id: str,
    observed_at: Optional[datetime] = None,
    ttl_days: Optional[Mapping[str, int]] = None,
) -> ExtractionResult:
    """ParsedSOSRecord -> claims. SOS publishes no contact channels we use."""
    _require_snapshot(source_snapshot_id)
    ts = _utc(observed_at)
    return ExtractionResult(claims=_claims_from_specs(
        record, SOS_FIELDS, source_snapshot_id=source_snapshot_id, observed_at=ts,
        ttl_days=ttl_days, extractor_version=SOS_EXTRACTOR_VERSION,
    ))


# ---------------------------------------------------------------- company site

def extract_company_site_contacts(
    contact_block: Any,
    *,
    source_snapshot_id: str,
    observed_at: Optional[datetime] = None,
    ttl_days: Optional[Mapping[str, int]] = None,
) -> ExtractionResult:
    """Regex-derived contact block from company_site/parser.py -> claims + contacts.

    Expects attributes/keys: `phones`, `emails`, `addresses` (lists) and
    optionally `website`. Each item is 'observed' (the page shows it).
    """
    _require_snapshot(source_snapshot_id)
    ts = _utc(observed_at)
    expires = ts + timedelta(days=_ttl(ttl_days, "site_contact", "company_site"))
    result = ExtractionResult()

    def add(claim_field: str, channel: Optional[str], raw_items: Any) -> None:
        seen: set[str] = set()
        items = _clean(raw_items) or []
        if not isinstance(items, list):
            items = [items]
        for item in items:
            key = str(item).lower()
            if key in seen:
                continue
            seen.add(key)
            result.claims.append(ClaimCandidate(
                field=claim_field, value=item, observed_or_inferred=OBSERVED,
                confidence=SITE_CONTACT_CONFIDENCE, valid_from=ts, observed_at=ts,
                expires_at=expires, source_snapshot_id=source_snapshot_id,
                extractor_version=SITE_CONTACT_EXTRACTOR_VERSION,
            ))
            if channel:
                result.contacts.append(
                    ContactCandidate(channel, str(item), "company_site", source_snapshot_id, ts))

    add("site_contact_phone", "phone", _read(contact_block, "phones"))
    add("site_contact_email", "email", _read(contact_block, "emails"))
    add("site_contact_address", None, _read(contact_block, "addresses"))
    website = _clean(_read(contact_block, "website"))
    if website:
        result.contacts.append(ContactCandidate("website", website, "company_site", source_snapshot_id, ts))
    return result