"""Address canonicalization. Pure functions, no I/O, no geocoding (v0).

Splits an address into street/city/county/state/zip. If a component cannot be
confidently resolved it is left as None and `normalization_status = "partial"`
(never guessed). The resolver treats partial addresses as weaker match signals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

_STATE_PAIRS = (
    "AL Alabama,AK Alaska,AZ Arizona,AR Arkansas,CA California,CO Colorado,CT Connecticut,"
    "DE Delaware,DC District of Columbia,FL Florida,GA Georgia,HI Hawaii,ID Idaho,IL Illinois,"
    "IN Indiana,IA Iowa,KS Kansas,KY Kentucky,LA Louisiana,ME Maine,MD Maryland,"
    "MA Massachusetts,MI Michigan,MN Minnesota,MS Mississippi,MO Missouri,MT Montana,"
    "NE Nebraska,NV Nevada,NH New Hampshire,NJ New Jersey,NM New Mexico,NY New York,"
    "NC North Carolina,ND North Dakota,OH Ohio,OK Oklahoma,OR Oregon,PA Pennsylvania,"
    "RI Rhode Island,SC South Carolina,SD South Dakota,TN Tennessee,TX Texas,UT Utah,"
    "VT Vermont,VA Virginia,WA Washington,WV West Virginia,WI Wisconsin,WY Wyoming"
)
STATE_CODES: dict[str, str] = {}
STATE_NAMES: dict[str, str] = {}
for _p in _STATE_PAIRS.split(","):
    _code, _name = _p.split(" ", 1)
    STATE_CODES[_code] = _name
    STATE_NAMES[_name.lower()] = _code

_TOKEN_MAP = {
    "street": "st", "str": "st", "avenue": "ave", "av": "ave", "boulevard": "blvd",
    "road": "rd", "drive": "dr", "lane": "ln", "court": "ct", "place": "pl",
    "terrace": "ter", "circle": "cir", "parkway": "pkwy", "highway": "hwy",
    "square": "sq", "suite": "ste", "apartment": "apt", "floor": "fl",
    "building": "bldg", "room": "rm", "north": "n", "south": "s", "east": "e",
    "west": "w", "northeast": "ne", "northwest": "nw", "southeast": "se",
    "southwest": "sw",
}
_STREET_SUFFIXES = frozenset({
    "st", "ave", "blvd", "rd", "dr", "ln", "ct", "pl", "ter", "cir", "pkwy",
    "hwy", "sq", "way", "loop", "trl", "aly", "plz", "row", "pike",
})
_UNIT_WORDS = frozenset({"ste", "apt", "unit", "fl", "bldg", "rm"})

_ZIP_RE = re.compile(r"(?:^|[\s,])(?P<zip>\d{5})(?:-(?P<zip4>\d{4}))?\s*$")
_COUNTRY_RE = re.compile(r"[,\s]+(?:usa|u\.s\.a\.|united states)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class NormalizedAddress:
    original: str
    street: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None      # 5-digit
    zip4: Optional[str] = None
    normalization_status: str = "empty"  # complete | partial | empty


def _blank(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = re.sub(r"\s+", " ", str(v)).strip(" ,")
    return v or None


def _clean_street(text: str) -> str:
    t = re.sub(r"\bp\.?\s*o\.?\s*box\b", "po box", text.lower())
    t = re.sub(r"[.,]", " ", t).replace("#", " # ")
    tokens = ["unit" if tok == "#" else _TOKEN_MAP.get(tok, tok) for tok in t.split()]
    return " ".join(tokens)


def _clean_place(text: str) -> str:
    t = re.sub(r"[.,]", " ", text)
    return re.sub(r"\s+", " ", t).strip().title()


def _clean_county(text: str) -> str:
    t = re.sub(r"\bcounty\b", "", text, flags=re.IGNORECASE)
    return _clean_place(t)


def _normalize_state(text: str) -> Optional[str]:
    t = text.strip().strip(".").strip()
    if t.upper() in STATE_CODES:
        return t.upper()
    return STATE_NAMES.get(t.lower())


def _pop_state(head: str, zip_found: bool) -> tuple[str, Optional[str]]:
    tokens = [t for t in re.split(r"[\s,]+", head.strip()) if t]
    for n in (2, 1):                      # try two-word names first ("New York")
        if len(tokens) >= n:
            cand = " ".join(tokens[-n:])
            code = _normalize_state(cand)
            if code and (zip_found or cand.isupper() or n == 2 or len(cand) > 2):
                rest = head.rstrip()
                rest = rest[: len(rest) - len(cand)].rstrip(" ,")
                return rest, code
    return head, None


def _split_street_city(one: str) -> tuple[str, Optional[str]]:
    """Heuristic split when no comma separates street from city."""
    tokens = one.split()
    lowered = [_TOKEN_MAP.get(t.lower().strip(".,"), t.lower().strip(".,")) for t in tokens]
    if lowered[:2] == ["po", "box"] and len(tokens) >= 3:
        end = 3
    else:
        idx = max((i for i, t in enumerate(lowered) if t in _STREET_SUFFIXES and i >= 1), default=None)
        if idx is None:
            return one, None
        end = idx + 1
        if end < len(tokens) and lowered[end] in _UNIT_WORDS and end + 1 < len(tokens):
            end += 2
        elif end < len(tokens) and tokens[end].startswith("#"):
            end += 1
    city = " ".join(tokens[end:]) or None
    return " ".join(tokens[:end]), city


def _parse_raw(raw: str) -> dict:
    text = re.sub(r"\s+", " ", raw.replace("\n", ", ")).strip(" ,")
    text = _COUNTRY_RE.sub("", text)
    out: dict = {}
    m = _ZIP_RE.search(text)
    if m:
        out["zip"], out["zip4"] = m.group("zip"), m.group("zip4")
        text = text[: m.start()].strip(" ,")
    text, state = _pop_state(text, zip_found=bool(m))
    out["state"] = state
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 2:
        out["street"], out["city"] = " ".join(parts[:-1]), parts[-1]
    elif len(parts) == 1:
        out["street"], out["city"] = _split_street_city(parts[0])
    return out


def normalize_address(
    raw: Optional[str] = None,
    *,
    street: Optional[str] = None,
    city: Optional[str] = None,
    county: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None,
) -> NormalizedAddress:
    """Normalize a raw address string and/or structured components.

    Explicit components override what is parsed from `raw`.
    """
    parsed = _parse_raw(raw) if raw and str(raw).strip() else {}
    s = _blank(street) or parsed.get("street")
    c = _blank(city) or parsed.get("city")
    co = _blank(county)
    st_raw = _blank(state)
    st = _normalize_state(st_raw) if st_raw else parsed.get("state")
    z_raw = _blank(zip_code) or parsed.get("zip")
    z4 = parsed.get("zip4")
    z = None
    if z_raw:
        digits = re.sub(r"\D", "", z_raw)
        if len(digits) >= 5:
            z = digits[:5]
            if len(digits) == 9:
                z4 = digits[5:]

    n_street = _clean_street(s) if s else None
    n_city = _clean_place(c) if c else None
    n_county = _clean_county(co) if co else None

    original = raw if raw else ", ".join(x for x in (street, city, state, zip_code) if x)
    if not any((n_street, n_city, n_county, st, z)):
        return NormalizedAddress(original=original or "", normalization_status="empty")
    complete = all((n_street, n_city, st, z))
    return NormalizedAddress(
        original=original or "", street=n_street, city=n_city, county=n_county,
        state=st, zip_code=z, zip4=z4,
        normalization_status="complete" if complete else "partial",
    )


def address_key(addr: NormalizedAddress) -> Optional[str]:
    """Stable comparison key, or None when too incomplete to compare safely."""
    if not addr.street:
        return None
    if addr.zip_code:
        tail = addr.zip_code
    elif addr.city and addr.state:
        tail = f"{addr.city.lower()}/{addr.state}"
    else:
        return None
    return f"{addr.street}|{tail}"


def addresses_match(a: NormalizedAddress, b: NormalizedAddress) -> bool:
    ka, kb = address_key(a), address_key(b)
    return ka is not None and ka == kb