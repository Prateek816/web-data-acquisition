"""Business-name canonicalization. Pure functions, no I/O.

Rules: strip legal suffixes (Inc/LLC/Corp...), lowercase, remove punctuation,
collapse whitespace. The original string is always kept alongside the
normalized form. DBA / AKA parts are split out as alternate names.

The normalized name is a matching *feature* only, never a sole match key.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

LEGAL_SUFFIXES = frozenset({
    "inc", "incorporated", "llc", "corp", "corporation", "co", "company",
    "ltd", "limited", "lp", "llp", "lllp", "pc", "pllc", "plc",
})

_DBA_SPLIT_RE = re.compile(
    r"\s*(?:\bd\s*/\s*b\s*/\s*a\b|\bdba\b|\bdoing business as\b|\ba\s*/\s*k\s*/\s*a\b|\baka\b)\s*",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class NormalizedName:
    original: str
    normalized: str
    alt_names: tuple[str, ...] = ()   # normalized DBA/AKA names
    status: str = "complete"          # complete | empty


def _canon(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("&", " and ")
    t = re.sub(r"[.'\u2019`]", "", t)          # L.L.C. -> llc, O'Brien -> obrien
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return t.strip()


def _clean(text: str) -> str:
    tokens = _canon(text).split()
    while len(tokens) > 1 and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    if len(tokens) > 1 and tokens[0] == "the":
        tokens.pop(0)
    return " ".join(tokens)


def normalize_name(raw: Optional[str]) -> NormalizedName:
    if raw is None or not str(raw).strip():
        return NormalizedName(original=raw or "", normalized="", status="empty")
    original = str(raw)
    parts = [p for p in _DBA_SPLIT_RE.split(original) if p and p.strip()]
    cleaned = [_clean(p) for p in parts]
    cleaned = [c for c in cleaned if c]
    if not cleaned:
        return NormalizedName(original=original, normalized="", status="empty")
    primary = cleaned[0]
    alts: list[str] = []
    for c in cleaned[1:]:
        if c != primary and c not in alts:
            alts.append(c)
    return NormalizedName(original=original, normalized=primary, alt_names=tuple(alts))


def _ratio(x: str, y: str) -> float:
    if not x or not y:
        return 0.0
    return SequenceMatcher(None, x, y).ratio()


def token_set_ratio(a: str, b: str) -> float:
    """Token-set similarity in [0, 1] (order-insensitive, subset-tolerant).

    Expects already-normalized strings. Stdlib-only equivalent of the classic
    fuzzy 'token set ratio'; swap for rapidfuzz later if measured need arises.
    """
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    inter = " ".join(sorted(ta & tb))
    rest_a = " ".join(sorted(ta - tb))
    rest_b = " ".join(sorted(tb - ta))
    t1 = f"{inter} {rest_a}".strip()
    t2 = f"{inter} {rest_b}".strip()
    return max(_ratio(inter, t1), _ratio(inter, t2), _ratio(t1, t2))


def name_similarity(a: Optional[str], b: Optional[str]) -> float:
    """Best similarity across primary and DBA names of two raw business names."""
    na, nb = normalize_name(a), normalize_name(b)
    if na.status == "empty" or nb.status == "empty":
        return 0.0
    names_a = (na.normalized, *na.alt_names)
    names_b = (nb.normalized, *nb.alt_names)
    return max(token_set_ratio(x, y) for x in names_a for y in names_b)