from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import anyio
from pydantic import HttpUrl

from launch_collector.batch import IngestRequest
from launch_collector.collecting import CollectionLimits, collect_brand, content_hash
from launch_collector.errors import CollectionError
from launch_collector.models import PostContent, SourceKey
from launch_collector.paik import parse_list

if TYPE_CHECKING:
    from launch_collector.adapters import Candidate, ListPage

FIXTURES = Path(__file__).parent / "fixtures" / "paik"


def sample_content(candidate: Candidate) -> PostContent:
    return PostContent(
        source_key=candidate.source_key,
        source_url=candidate.source_url,
        title=candidate.title,
        body_text="",
        image_urls=(HttpUrl("https://paikdabang.com/wp-content/uploads/test.png"),),
        thumbnail_url=HttpUrl("https://paikdabang.com/wp-content/uploads/test.png"),
        posted_on=candidate.posted_on,
        release_on=None,
        is_seasonal=None,
        is_limited=None,
        notice_period_text=None,
        observed_at=datetime.now(UTC),
    )


@dataclass(frozen=True, slots=True)
class FixtureAdapter:
    failed_key: SourceKey | None = None
    failed_page: int | None = None

    @property
    def brand_id(self) -> Literal["paik"]:
        return "paik"

    async def list_page(self, page: int) -> ListPage:
        if page == self.failed_page:
            raise CollectionError("HTTP_503")
        return parse_list((FIXTURES / f"list-page{page}.html").read_text(encoding="utf-8"), page)

    async def fetch_detail(self, candidate: Candidate) -> PostContent:
        if candidate.source_key == self.failed_key:
            raise CollectionError("HTTP_404")
        return sample_content(candidate)


def test_collection_when_requested_scope_crosses_page_boundary() -> None:
    # Given
    adapter = FixtureAdapter()

    async def run() -> IngestRequest:
        result = await collect_brand(adapter, CollectionLimits(max_posts=12, max_pages=2))
        assert result.pages_read == 2
        assert result.has_more
        return result.request

    # When
    request = anyio.run(run)
    # Then
    assert len(request.p_payload.posts) == 12
    assert len({post.source_key for post in request.p_payload.posts}) == 12
    assert IngestRequest.model_validate_json(request.model_dump_json()) == request
    assert all(post.auto_decision == "needs_review" for post in request.p_payload.posts)


def test_collection_when_one_detail_fails_preserves_other_posts() -> None:
    # Given
    first = parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    adapter = FixtureAdapter(failed_key=first.candidates[1].source_key)

    async def run() -> IngestRequest:
        return (await collect_brand(adapter, CollectionLimits(max_posts=3))).request

    # When
    batch = anyio.run(run).p_payload
    # Then
    assert batch.status == "partial"
    assert len(batch.seen) == 3
    assert len(batch.posts) == 2
    assert batch.failed_details[0].source_key == first.candidates[1].source_key
    assert batch.failed_details[0].error_code == "HTTP_404"


def test_collection_when_first_list_fails_is_not_empty_success() -> None:
    # Given
    adapter = FixtureAdapter(failed_page=1)

    async def run() -> IngestRequest:
        return (await collect_brand(adapter, CollectionLimits())).request

    # When
    batch = anyio.run(run).p_payload
    # Then
    assert batch.status == "failed"
    assert batch.error_code == "HTTP_503"
    assert batch.seen == batch.posts == batch.failed_details == ()


def test_collection_when_later_list_fails_retains_completed_scope() -> None:
    # Given
    adapter = FixtureAdapter(failed_page=2)

    async def run() -> IngestRequest:
        return (await collect_brand(adapter, CollectionLimits(max_posts=12))).request

    # When
    batch = anyio.run(run).p_payload
    # Then
    assert batch.list_status == "partial"
    assert len(batch.posts) == 10
    assert batch.error_code == "HTTP_503"


def test_hash_when_only_observation_time_changes_remains_stable() -> None:
    # Given
    first = parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    content = sample_content(first.candidates[0])
    # When
    repeated = content.model_copy(update={"observed_at": datetime(2027, 1, 1, tzinfo=UTC)})
    # Then
    assert content_hash(content) == content_hash(repeated)
    assert content_hash(content) != content_hash(content.model_copy(update={"body_text": "변경"}))
