"""Official news-list and article extraction, independent of launch classification."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Literal

from selectolax.lexbor import LexborHTMLParser

from launch_collector.adapters import Candidate, ListPage
from launch_collector.errors import CollectionError
from launch_collector.models import PostContent
from launch_collector.urls import canonical_post_url, official_url, post_key

if TYPE_CHECKING:
    from pydantic import HttpUrl
    from selectolax.lexbor import LexborNode

    from launch_collector.network import Fetcher


def parse_date(text: str) -> date | None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text.strip()):
        return None
    try:
        return date.fromisoformat(text.strip())
    except ValueError:
        return None


def parse_row(row: LexborNode) -> Candidate | None:
    cell = row.css_first("td.tit")
    if cell is None:
        if "등록된 게시글이 없습니다" in row.text():
            return None
        raise CollectionError("LIST_LAYOUT_CHANGED")
    link = cell.css_first("a")
    if link is None:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    href = link.attributes.get("href")
    title = link.text(strip=True)
    if not href or not title:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    url = canonical_post_url(href)
    date_cell = row.css_first("td.date")
    return Candidate(
        source_key=post_key(url),
        source_url=url,
        title=title,
        posted_on=parse_date(date_cell.text(strip=True)) if date_cell else None,
        thumbnail_url=None,
    )


def parse_list(html: str, page: int) -> ListPage:
    tree = LexborHTMLParser(html)
    table = tree.css_first("table")
    if table is None or table.css_first("th.tit") is None or table.css_first("th.date") is None:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    candidates = tuple(
        candidate for row in table.css("tbody tr") if (candidate := parse_row(row)) is not None
    )
    explicit_empty = not candidates and "등록된 게시글이 없습니다" in table.text()
    if not candidates and not explicit_empty:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    next_pages: list[int] = []
    for link in tree.css("a.page-numbers"):
        href = link.attributes.get("href")
        if href:
            url = official_url(href)
            match = re.fullmatch(r"/news/page/(\d+)/", url.path or "")
            if match and int(match[1]) > page:
                next_pages.append(int(match[1]))
    return ListPage(
        candidates=candidates,
        next_page=min(next_pages) if next_pages else None,
        board_recognized=True,
        explicit_empty=explicit_empty,
    )


def parse_detail(html: str, candidate: Candidate) -> PostContent:
    tree = LexborHTMLParser(html)
    title_node = tree.css_first(".view_wrap .view_tit h2")
    body = tree.css_first(".view_wrap .view_cont")
    if title_node is None or body is None:
        raise CollectionError("DETAIL_LAYOUT_CHANGED")
    for subject in title_node.css(".subject"):
        subject.decompose()
    title = title_node.text(strip=True)
    if not title:
        raise CollectionError("DETAIL_LAYOUT_CHANGED")
    for node in body.css("script,style,iframe,noscript"):
        node.decompose()
    images: list[HttpUrl] = []
    for node in body.css("img"):
        value = node.attributes.get("data-src") or node.attributes.get("data-lazy-src")
        value = value or node.attributes.get("src")
        if not value or value.startswith(("data:", "javascript:")):
            continue
        try:
            url = official_url(value, str(candidate.source_url))
        except CollectionError:
            continue
        if url not in images:
            images.append(url)
    text = body.text(separator="\n", strip=True).strip()
    if not text and not images:
        raise CollectionError("EMPTY_CONTENT")
    date_node = tree.css_first(".view_wrap .view_desc li")
    posted_on = parse_date(date_node.text(strip=True)) if date_node else None
    return PostContent(
        source_key=candidate.source_key,
        source_url=candidate.source_url,
        title=title,
        body_text=text,
        image_urls=tuple(images),
        thumbnail_url=candidate.thumbnail_url or (images[0] if images else None),
        posted_on=posted_on or candidate.posted_on,
        release_on=None,
        is_seasonal=None,
        is_limited=None,
        notice_period_text=None,
        observed_at=datetime.now(UTC),
    )


@dataclass(frozen=True, slots=True)
class PaikAdapter:
    fetcher: Fetcher

    @property
    def brand_id(self) -> Literal["paik"]:
        return "paik"

    async def list_page(self, page: int) -> ListPage:
        path = "/news/" if page == 1 else f"/news/page/{page}/"
        resource = await self.fetcher.fetch(official_url(path))
        return parse_list(resource.html(), page)

    async def fetch_detail(self, candidate: Candidate) -> PostContent:
        resource = await self.fetcher.fetch(candidate.source_url)
        return parse_detail(resource.html(), candidate)
