"""Phone canonicalization to E.164, keeping the original formatting alongside.

US/NANP is the v0 default region. Numbers that cannot be validated get
`e164 = None` and a non-"valid" status rather than a guess.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_EXT_RE = re.compile(r"(?:\b(?:ext|extension)\.?|x|#)\s*(\d{1,6})\s*$", re.IGNORECASE)
_NANP_RE = re.compile(r"^[2-9]\d{2}[2-9]\d{6}$")


@dataclass(frozen=True)
class NormalizedPhone:
    original: str
    e164: Optional[str] = None          # e.g. "+15105550134"
    digits: Optional[str] = None        # national significant digits, e.g. "5105550134"
    extension: Optional[str] = None
    status: str = "empty"               # valid | international | invalid | empty


def normalize_phone(raw: Optional[str], default_region: str = "US") -> NormalizedPhone:
    if raw is None or not str(raw).strip():
        return NormalizedPhone(original=raw or "")
    original = str(raw)
    text = original.strip()

    ext = None
    m = _EXT_RE.search(text)
    if m:
        ext = m.group(1)
        text = text[: m.start()].strip()

    has_plus = text.startswith("+")
    digits = re.sub(r"\D", "", text)

    if default_region == "US" and not (has_plus and not digits.startswith("1")):
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) == 10:
            if _NANP_RE.match(digits):
                return NormalizedPhone(original, f"+1{digits}", digits, ext, "valid")
            return NormalizedPhone(original, None, digits, ext, "invalid")

    if has_plus and 8 <= len(digits) <= 15:
        return NormalizedPhone(original, f"+{digits}", None, ext, "international")

    return NormalizedPhone(original, None, digits or None, ext, "invalid")


def phones_match(a: Optional[str], b: Optional[str]) -> bool:
    """True only when both numbers validate and their E.164 forms are equal."""
    pa, pb = normalize_phone(a), normalize_phone(b)
    return pa.e164 is not None and pa.e164 == pb.e164