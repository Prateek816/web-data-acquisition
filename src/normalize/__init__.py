"""Deterministic canonicalization helpers. Pure functions, no I/O, no network."""
from __future__ import annotations

from typing import Optional

from .addresses import NormalizedAddress, address_key, addresses_match, normalize_address
from .domains import (
    domain_from_email,
    is_generic_domain,
    is_joinable_domain,
    normalize_domain,
)
from .names import NormalizedName, name_similarity, normalize_name, token_set_ratio
from .phones import NormalizedPhone, normalize_phone, phones_match

__all__ = [
    "NormalizedAddress", "address_key", "addresses_match", "normalize_address",
    "domain_from_email", "is_generic_domain", "is_joinable_domain", "normalize_domain",
    "NormalizedName", "name_similarity", "normalize_name", "token_set_ratio",
    "NormalizedPhone", "normalize_phone", "phones_match",
    "normalize_contact_value",
]


def normalize_contact_value(channel: str, value: str) -> Optional[str]:
    """Canonical form of a ContactPoint value (used by the coordinator before persisting).

    phone   -> E.164 (or None if invalid)
    email   -> lowercased, stripped
    website -> normalized domain (or None if invalid)
    """
    if value is None:
        return None
    channel = channel.strip().lower()
    if channel == "phone":
        return normalize_phone(value).e164
    if channel == "email":
        v = value.strip().lower()
        return v if "@" in v and " " not in v else None
    if channel == "website":
        return normalize_domain(value)
    return value.strip() or None