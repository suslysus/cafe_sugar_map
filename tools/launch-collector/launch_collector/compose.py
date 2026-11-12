"""Official Compose public-news extraction, without release-date inference."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal
from urllib.parse import parse_qs, urlsplit

from selectolax.lexbor import LexborHTMLParser

from launch_collector.adapters import Candidate, ListPage
from launch_collector.errors import CollectionError
from launch_collector.html_content import content_from_body
from launch_collector.models import PostContent, SourceKey
from launch_collector.paik import parse_date
from launch_collector.urls import brand_url

if TYPE_CHECKING:
    from selectolax.lexbor import LexborNode

    from launch_collector.network import Fetcher


def parse_row(row: LexborNode) -> Candidate:
    link = row.css_first("a.doc_link")
    title = row.css_first(".doc_title")
    if link is None or title is None or not title.text(strip=True):
        raise CollectionError("LIST_LAYOUT_CHANGED")
    href = link.attributes.get("href")
    if not href:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    url = brand_url(href, "compose")
    document = re.fullmatch(r"/news/(\d+)/?", url.path or "")
    if document is None:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    canonical = brand_url(f"/news/{document[1]}", "compose")
    date_node = row.css_first(".regdate")
    thumbnail = row.css_first(".image_area img")
    image = thumbnail.attributes.get("src") if thumbnail else None
    return Candidate(
        source_key=SourceKey(f"news:{document[1]}"),
        source_url=canonical,
        title=title.text(strip=True),
        posted_on=parse_date(date_node.text(strip=True)[:10]) if date_node else None,
        thumbnail_url=brand_url(image, "compose") if image else None,
    )


def parse_list(html: str, page: int) -> ListPage:
    tree = LexborHTMLParser(html)
    board = tree.css_first("#board_list")
    if board is None:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    listing = board.css_first("ul.webzine_h")
    rows = board.css("ul.webzine_h > li") if listing else []
    candidates = tuple(parse_row(row) for row in rows)
    empty = board.css_first(".no_documents")
    explicit_empty = not candidates and empty is not None and "등록된 글이 없습니다" in empty.text()
    if not candidates and not explicit_empty:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    next_pages: list[int] = []
    for link in tree.css(".pagination a"):
        href = link.attributes.get("href")
        if not href:
            continue
        url = brand_url(href, "compose")
        parts = urlsplit(str(url))
        values = parse_qs(parts.query).get("page", [])
        if parts.path.rstrip("/") == "/news" and len(values) == 1 and values[0].isdigit():
            target = int(values[0])
            if target > page:
                next_pages.append(target)
    return ListPage(
        candidates=candidates,
        next_page=min(next_pages) if next_pages else None,
        board_recognized=True,
        explicit_empty=explicit_empty,
    )


def parse_detail(html: str, candidate: Candidate) -> PostContent:
    tree = LexborHTMLParser(html)
    body = tree.css_first(
        ".board_read .read_body .rhymix_content, .board_read .read_body .xe_content"
    )
    if body is None:
        raise CollectionError("DETAIL_LAYOUT_CHANGED")
    return content_from_body(body, candidate, "compose")


@dataclass(frozen=True, slots=True)
class ComposeAdapter:
    fetcher: Fetcher

    @property
    def brand_id(self) -> Literal["compose"]:
        return "compose"

    async def list_page(self, page: int) -> ListPage:
        url = brand_url(f"/news?page={page}", "compose")
        resource = await self.fetcher.fetch(url)
        return parse_list(resource.html(), page)

    async def fetch_detail(self, candidate: Candidate) -> PostContent:
        resource = await self.fetcher.fetch(candidate.source_url)
        return parse_detail(resource.html(), candidate)
