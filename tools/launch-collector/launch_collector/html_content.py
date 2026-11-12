"""Extract safe article text and official images without inferring launch facts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from launch_collector.errors import CollectionError
from launch_collector.models import PostContent
from launch_collector.urls import brand_url

if TYPE_CHECKING:
    from pydantic import HttpUrl
    from selectolax.lexbor import LexborNode

    from launch_collector.adapters import Candidate
    from launch_collector.models import BrandId


def content_from_body(body: LexborNode, candidate: Candidate, brand: BrandId) -> PostContent:
    for node in body.css("script,style,iframe,noscript,nav"):
        node.decompose()
    images: list[HttpUrl] = []
    for image in body.css("img"):
        raw = (
            image.attributes.get("data-src")
            or image.attributes.get("data-lazy-src")
            or image.attributes.get("src")
        )
        if not raw or raw.startswith(("data:", "javascript:")):
            continue
        try:
            url = brand_url(raw, brand, str(candidate.source_url))
        except CollectionError:
            continue
        if url not in images:
            images.append(url)
    text = body.text(separator="\n", strip=True).strip()
    if not text and not images:
        raise CollectionError("EMPTY_CONTENT")
    return PostContent(
        source_key=candidate.source_key,
        source_url=candidate.source_url,
        title=candidate.title,
        body_text=text,
        image_urls=tuple(images),
        thumbnail_url=candidate.thumbnail_url or (images[0] if images else None),
        posted_on=candidate.posted_on,
        release_on=None,
        is_seasonal=None,
        is_limited=None,
        notice_period_text=None,
        observed_at=datetime.now(UTC),
    )
