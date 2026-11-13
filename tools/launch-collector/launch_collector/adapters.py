"""Interface for subsequent brand-specific network adapters."""

from __future__ import annotations

from datetime import date
from typing import Protocol

from pydantic import Field, HttpUrl

from launch_collector.models import BrandId, FrozenModel, PostContent, PostKey, Title


class Candidate(FrozenModel):
    source_key: PostKey
    source_url: HttpUrl
    title: Title
    posted_on: date | None
    thumbnail_url: HttpUrl | None


class ListPage(FrozenModel):
    candidates: tuple[Candidate, ...]
    next_page: int | None = Field(default=None, ge=1)
    board_recognized: bool
    explicit_empty: bool


class BrandAdapter(Protocol):
    """An adapter extracts source data; it does not classify or write to DB."""

    @property
    def brand_id(self) -> BrandId: ...

    async def list_page(self, page: int) -> ListPage: ...

    async def fetch_detail(self, candidate: Candidate) -> PostContent: ...
