"""Official Paik URLs and stable post identifiers."""

from __future__ import annotations

from hashlib import sha256
from typing import Final, assert_never
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

from pydantic import HttpUrl, ValidationError

from launch_collector.errors import CollectionError
from launch_collector.models import BrandId, SourceKey

SITE: Final = "https://paikdabang.com/"


def brand_url(value: str, brand: BrandId, base: str | None = None) -> HttpUrl:
    """Resolve only this brand's observed official site and media hosts."""
    match brand:
        case "paik":
            return official_url(value, base or SITE)
        case "mega":
            site = "https://www.mega-mgccoffee.com/"
            hosts = {"www.mega-mgccoffee.com", "mega-mgccoffee.com", "img.mega-mgccoffee.com"}
        case "compose":
            site = "https://composecoffee.com/"
            hosts = {"composecoffee.com", "www.composecoffee.com"}
        case "starbucks":
            site = "https://www.starbucks.co.kr/"
            hosts = {"www.starbucks.co.kr", "image.istarbucks.co.kr"}
        case unreachable:
            assert_never(unreachable)
    try:
        url = HttpUrl(urljoin(base or site, value))
    except ValidationError:
        raise CollectionError("INVALID_URL") from None
    if url.host not in hosts or url.port not in {80, 443} or url.username or url.password:
        raise CollectionError("INVALID_URL")
    parts = urlsplit(str(url))
    return HttpUrl(urlunsplit(("https", parts.netloc, parts.path, parts.query, "")))


def official_url(value: str, base: str = SITE) -> HttpUrl:
    try:
        url = HttpUrl(urljoin(base, value))
    except ValidationError:
        raise CollectionError("INVALID_URL") from None
    if (
        url.host not in {"paikdabang.com", "www.paikdabang.com"}
        or url.port not in {80, 443}
        or url.username
        or url.password
    ):
        raise CollectionError("INVALID_URL")
    parts = urlsplit(str(url))
    path = quote(unquote(parts.path), safe="/-._~")
    return HttpUrl(urlunsplit(("https", "paikdabang.com", path, parts.query, "")))


def canonical_post_url(value: str) -> HttpUrl:
    url = official_url(value)
    parts = urlsplit(str(url))
    if not parts.path.startswith("/post_news/") or parts.path == "/post_news/":
        raise CollectionError("INVALID_URL")
    return HttpUrl(urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/") + "/", "", "")))


def post_key(url: HttpUrl) -> SourceKey:
    canonical = canonical_post_url(str(url))
    return SourceKey("url:" + sha256(str(canonical).encode("utf-8")).hexdigest())
