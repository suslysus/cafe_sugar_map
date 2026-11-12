"""Bounded multi-page collection with explicit detail failures and stable hashes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import Field

from launch_collector.batch import BrandBatch, IngestRequest, ListStatus
from launch_collector.errors import CollectionError
from launch_collector.models import (
    CollectedPost,
    FailedDetail,
    FrozenModel,
    PostContent,
    SeenPost,
    SourceKey,
)

if TYPE_CHECKING:
    from launch_collector.adapters import BrandAdapter, Candidate


class CollectionLimits(FrozenModel):
    max_posts: int = Field(default=10, ge=1, le=200)
    max_pages: int = Field(default=3, ge=1, le=20)


@dataclass(frozen=True, slots=True)
class CollectionResult:
    request: IngestRequest
    pages_read: int
    has_more: bool | None


def content_hash(content: PostContent) -> str:
    fields = {
        "title": content.title,
        "body_text": content.body_text,
        "image_urls": [str(url) for url in content.image_urls],
        "thumbnail_url": str(content.thumbnail_url) if content.thumbnail_url else None,
        "posted_on": content.posted_on.isoformat() if content.posted_on else None,
        "release_on": content.release_on.isoformat() if content.release_on else None,
        "is_seasonal": content.is_seasonal,
        "is_limited": content.is_limited,
        "notice_period_text": content.notice_period_text,
    }
    raw = json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def review_candidate(content: PostContent) -> CollectedPost:
    """Extraction is not launch approval; leave classification to a later change."""
    return CollectedPost(
        source_key=content.source_key,
        source_url=content.source_url,
        title=content.title,
        body_text=content.body_text,
        image_urls=content.image_urls,
        thumbnail_url=content.thumbnail_url,
        posted_on=content.posted_on,
        release_on=content.release_on,
        is_seasonal=content.is_seasonal,
        is_limited=content.is_limited,
        notice_period_text=content.notice_period_text,
        observed_at=content.observed_at,
        auto_decision="needs_review",
        evidence={"reason": "collection_only_not_classified"},
        content_hash=content_hash(content),
    )


@dataclass(frozen=True, slots=True)
class Selection:
    entries: tuple[tuple[Candidate, datetime], ...]
    pages_read: int
    has_more: bool | None
    status: ListStatus
    error_code: str | None


async def select_posts(adapter: BrandAdapter, limits: CollectionLimits) -> Selection:
    selected: dict[SourceKey, tuple[Candidate, datetime]] = {}
    list_status: ListStatus = "ok"
    error_code: str | None = None
    pages_read = 0
    has_more: bool | None = False
    page_number = 1
    while pages_read < limits.max_pages:
        try:
            page = await adapter.list_page(page_number)
        except CollectionError as error:
            list_status = "partial" if selected else "failed"
            error_code = error.code
            has_more = None
            break
        if not page.board_recognized or (not page.candidates and not page.explicit_empty):
            list_status = "partial" if selected else "failed"
            error_code, has_more = "LIST_LAYOUT_CHANGED", None
            break
        pages_read += 1
        observed_at = datetime.now(UTC)
        remaining = False
        for candidate in page.candidates:
            if candidate.source_key in selected:
                continue
            if len(selected) >= limits.max_posts:
                remaining = True
                break
            selected[candidate.source_key] = (candidate, observed_at)
        has_more = remaining or page.next_page is not None
        if len(selected) >= limits.max_posts or page.next_page is None:
            break
        if page.next_page <= page_number:
            list_status, error_code, has_more = "partial", "INVALID_PAGINATION", None
            break
        page_number = page.next_page
    return Selection(tuple(selected.values()), pages_read, has_more, list_status, error_code)


async def collect_brand(adapter: BrandAdapter, limits: CollectionLimits) -> CollectionResult:
    attempted_at = datetime.now(UTC)
    selected = await select_posts(adapter, limits)
    posts: list[CollectedPost] = []
    failures: list[FailedDetail] = []
    for candidate, _ in selected.entries:
        detail_attempt = datetime.now(UTC)
        try:
            posts.append(review_candidate(await adapter.fetch_detail(candidate)))
        except CollectionError as error:
            failures.append(
                FailedDetail(
                    source_key=candidate.source_key,
                    attempted_at=detail_attempt,
                    error_code=error.code,
                )
            )
    batch = BrandBatch(
        schema_version=1,
        run_id=uuid4(),
        brand_id=adapter.brand_id,
        attempted_at=attempted_at,
        list_status=selected.status,
        seen=tuple(
            SeenPost(source_key=candidate.source_key, observed_at=stamp)
            for candidate, stamp in selected.entries
        ),
        posts=tuple(posts),
        failed_details=tuple(failures),
        error_code=selected.error_code,
    )
    return CollectionResult(IngestRequest(p_payload=batch), selected.pages_read, selected.has_more)
