"""Extract the official Mega public event gallery and article bodies."""

from __future__ import annotations

import re
from base64 import b64decode
from binascii import Error as Base64Error
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Final, Literal
from urllib.parse import parse_qs, unquote, urlsplit

from selectolax.lexbor import LexborHTMLParser

from launch_collector.adapters import Candidate, ListPage
from launch_collector.errors import CollectionError
from launch_collector.html_content import content_from_body
from launch_collector.models import PostContent, SourceKey
from launch_collector.urls import brand_url

if TYPE_CHECKING:
    from pydantic import HttpUrl
    from selectolax.lexbor import LexborNode

    from launch_collector.network import Fetcher

SITE: Final = "https://www.mega-mgccoffee.com/bbs/"


def list_url(page: int) -> HttpUrl:
    return brand_url(f"{SITE}?bbs_category=3&bbs_page={page}", "mega")


def post_key(value: str) -> SourceKey:
    """Read the immutable article ID, excluding mutable listing-page context."""
    url = brand_url(value, "mega", SITE)
    if url.path != "/bbs/detail/" or url.host == "img.mega-mgccoffee.com":
        raise CollectionError("INVALID_URL")
    query = unquote(urlsplit(str(url)).query)
    try:
        payload = b64decode(query, validate=True).decode("ascii")
    except (Base64Error, UnicodeError, ValueError):
        raise CollectionError("INVALID_URL") from None
    fields = parse_qs(payload, keep_blank_values=True)
    ids = fields.get("bbs_idx", [])
    if (
        fields.get("bbs_category") != ["3"]
        or len(ids) != 1
        or not re.fullmatch(r"[1-9]\d*", ids[0])
    ):
        raise CollectionError("INVALID_URL")
    return SourceKey(f"event:{ids[0]}")


def parse_row(link: LexborNode) -> Candidate:
    raw = link.attributes.get("href", "")
    title = link.css_first(".cont_text_title")
    if not raw or title is None or not title.text(strip=True):
        raise CollectionError("LIST_LAYOUT_CHANGED")
    url = brand_url(raw, "mega", SITE)
    image = link.css_first(".cont_gallery_list_img img")
    image_src = image.attributes.get("src") if image else None
    return Candidate(
        source_key=post_key(str(url)),
        source_url=url,
        title=title.text(strip=True),
        posted_on=None,
        thumbnail_url=brand_url(image_src, "mega", SITE) if image_src else None,
    )


def parse_list(html: str, page: int) -> ListPage:
    tree = LexborHTMLParser(html)
    board = tree.css_first(".board_list_gallery")
    if board is None:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    candidates = tuple(parse_row(link) for link in board.css("ul > li > a"))
    empty = not candidates and any(
        marker in board.text()
        for marker in ("등록된 게시물이 없습니다", "등록된 게시글이 없습니다")
    )
    if not candidates and not empty:
        raise CollectionError("LIST_LAYOUT_CHANGED")
    following: list[int] = []
    for link in tree.css(".board_page a.board_page_link"):
        url = brand_url(link.attributes.get("href") or "", "mega", SITE)
        fields = parse_qs(urlsplit(str(url)).query)
        values = fields.get("bbs_page", [])
        if fields.get("bbs_category") == ["3"] and len(values) == 1 and values[0].isdigit():
            number = int(values[0])
            if number > page:
                following.append(number)
    return ListPage(
        candidates=candidates,
        next_page=min(following) if following else None,
        board_recognized=True,
        explicit_empty=empty,
    )


def parse_detail(html: str, candidate: Candidate) -> PostContent:
    tree = LexborHTMLParser(html)
    title = tree.css_first(".board_detail .board_detail_title h1")
    body = tree.css_first(".board_detail .board_detail_text")
    if title is None or body is None or not title.text(strip=True):
        raise CollectionError("DETAIL_LAYOUT_CHANGED")
    posted_on = candidate.posted_on
    info = tree.css_first(".board_detail_title_info")
    if info:
        found = re.search(r"\b\d{4}-\d{2}-\d{2}\b", info.text())
        if found:
            try:
                posted_on = date.fromisoformat(found[0])
            except ValueError:
                posted_on = None
    article = candidate.model_copy(update={"title": title.text(strip=True), "posted_on": posted_on})
    return content_from_body(body, article, "mega")


@dataclass(frozen=True, slots=True)
class MegaAdapter:
    fetcher: Fetcher

    @property
    def brand_id(self) -> Literal["mega"]:
        return "mega"

    async def list_page(self, page: int) -> ListPage:
        resource = await self.fetcher.fetch(list_url(page))
        return parse_list(resource.html(), page)

    async def fetch_detail(self, candidate: Candidate) -> PostContent:
        resource = await self.fetcher.fetch(candidate.source_url)
        return parse_detail(resource.html(), candidate)
