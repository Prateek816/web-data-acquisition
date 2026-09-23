"""Domain canonicalization. The canonical domain is the entity-resolution join key.

Lowercase, strip protocol / userinfo / port / path / leading `www.`, IDNA-encode.
Returns None for anything that isn't a plausible hostname (IPs, garbage).
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlsplit

_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?:(?!-)[a-z0-9-]{1,63}(?<!-)\.)+[a-z][a-z0-9-]{0,62}$"
)

# Shared / third-party domains that must NOT be used as an entity join key:
# many unrelated businesses share them.
GENERIC_DOMAINS = frozenset({
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com",
    "live.com", "msn.com", "comcast.net", "att.net", "sbcglobal.net", "protonmail.com",
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "yelp.com", "houzz.com", "angi.com", "homeadvisor.com", "thumbtack.com",
    "nextdoor.com", "google.com", "youtube.com", "wixsite.com", "weebly.com",
    "business.site", "squarespace.com", "godaddysites.com",
})


def normalize_domain(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip().lower()
    if not v:
        return None
    if "@" in v and "://" not in v:            # bare email -> its domain
        v = v.rsplit("@", 1)[1]
    try:
        host = urlsplit(v if "://" in v else "//" + v).hostname
    except ValueError:
        return None
    if not host:
        return None
    host = host.rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    return host if _HOST_RE.match(host) else None


def domain_from_email(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return None
    return normalize_domain(email.rsplit("@", 1)[1])


def is_generic_domain(domain: Optional[str]) -> bool:
    d = normalize_domain(domain)
    if d is None:
        return False
    return any(d == g or d.endswith("." + g) for g in GENERIC_DOMAINS)


def is_joinable_domain(domain: Optional[str]) -> bool:
    """True if the domain is valid and specific enough to use as a match key."""
    d = normalize_domain(domain)
    return d is not None and not is_generic_domain(d)