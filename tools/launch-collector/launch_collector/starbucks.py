"""Extract Starbucks Korea's public N01 news JSON without inferring launch facts."""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from typing import TYPE_CHECKING, Annotated, ClassVar, Final, Literal
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from selectolax.lexbor import LexborHTMLParser

from launch_collector.adapters import Candidate, ListPage
from launch_collector.errors import CollectionError
from launch_collector.html_content import content_from_body
from launch_collector.models import PostContent, SourceKey, Title
from launch_collector.paik import parse_date
from launch_collector.urls import brand_url

if TYPE_CHECKING:
    from launch_collector.network import FormFetcher

PAGE_SIZE: Final = 10


class _OfficialJson(BaseModel):
    # The official payload includes unrelated search/admin defaults; only used fields are parsed.
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, strict=True, extra="ignore")


class _NewsRow(_OfficialJson):
    seq: Annotated[int, Field(gt=0)]
    title: Title
    news_dt: str | None = None
    img_nm: str


class _NewsList(_OfficialJson):
    cnt: Annotated[int, Field(ge=0)]
    list: tuple[_NewsRow, ...]


class _NewsDetail(_OfficialJson):
    seq: Annotated[int, Field(gt=0)]
    content: Annotated[str, Field(min_length=1)]


class _NewsView(_OfficialJson):
    view: _NewsDetail


def parse_list(data: bytes, page: int) -> ListPage:
    """Require a recognized JSON board and its expected rows before accepting a page."""
    try:
        payload = _NewsList.model_validate_json(data)
    except ValidationError:
        raise CollectionError("LIST_LAYOUT_CHANGED") from None
    expected = min(PAGE_SIZE, max(0, payload.cnt - (page - 1) * PAGE_SIZE))
    if page < 1 or len(payload.list) != expected or (payload.cnt > 0 and not payload.list):
        raise CollectionError("LIST_LAYOUT_CHANGED")
    candidates = tuple(
        Candidate(
            source_key=SourceKey(f"news:{row.seq}"),
            source_url=brand_url(f"/whats_new/newsView.do?cate=N01&seq={row.seq}", "starbucks"),
            title=unescape(row.title),
            posted_on=parse_date(row.news_dt) if row.news_dt is not None else None,
            thumbnail_url=(
                brand_url(
                    "https://image.istarbucks.co.kr/upload/news/" + quote(row.img_nm, safe=""),
                    "starbucks",
                )
                if row.img_nm
                else None
            ),
        )
        for row in payload.list
    )
    return ListPage(
        candidates=candidates,
        next_page=page + 1 if page * PAGE_SIZE < payload.cnt else None,
        board_recognized=True,
        explicit_empty=payload.cnt == 0,
    )


def parse_detail(data: bytes, candidate: Candidate) -> PostContent:
    """Parse the matching official article's HTML from its JSON envelope."""
    try:
        detail = _NewsView.model_validate_json(data).view
    except ValidationError:
        raise CollectionError("DETAIL_LAYOUT_CHANGED") from None
    if candidate.source_key != f"news:{detail.seq}":
        raise CollectionError("DETAIL_LAYOUT_CHANGED")
    body = LexborHTMLParser(detail.content).body
    if body is None:
        raise CollectionError("DETAIL_LAYOUT_CHANGED")
    return content_from_body(body, candidate, "starbucks")


@dataclass(frozen=True, slots=True)
class StarbucksAdapter:
    fetcher: FormFetcher

    @property
    def brand_id(self) -> Literal["starbucks"]:
        return "starbucks"

    async def list_page(self, page: int) -> ListPage:
        resource = await self.fetcher.post_form(
            brand_url("/whats_new/newsListAjax.do", self.brand_id),
            {"cate": "N01", "pageIndex": str(page), "searchKeyword": "", "searchKey": "3"},
        )
        return parse_list(resource.data, page)

    async def fetch_detail(self, candidate: Candidate) -> PostContent:
        resource = await self.fetcher.post_form(
            brand_url("/whats_new/newsViewAjax.do", self.brand_id),
            {"seq": candidate.source_key.removeprefix("news:"), "view_yn": ""},
        )
        return parse_detail(resource.data, candidate)
