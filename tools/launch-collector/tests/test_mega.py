from __future__ import annotations

from base64 import b64encode
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
import httpx2
import pytest

from launch_collector.errors import CollectionError
from launch_collector.mega import MegaAdapter, parse_detail, parse_list, post_key
from launch_collector.network import HttpFetcher

if TYPE_CHECKING:
    from launch_collector.models import PostContent

FIXTURES = Path(__file__).parent / "fixtures" / "mega"


@pytest.mark.parametrize(("page", "next_page"), [(1, 2), (2, 3)])
def test_list_when_captured_official_gallery_has_twelve_rows(page: int, next_page: int) -> None:
    # Given
    html = (FIXTURES / f"list-page{page}.html").read_text(encoding="utf-8")
    # When
    result = parse_list(html, page)
    # Then
    assert len(result.candidates) == 12
    assert len({c.source_key for c in result.candidates}) == 12
    assert result.next_page == next_page
    assert all(c.thumbnail_url for c in result.candidates)
    assert all(c.posted_on is None for c in result.candidates)


@pytest.mark.parametrize(
    ("index", "posted"), [(1, date(2026, 10, 26)), (2, date(2026, 10, 20)), (3, date(2026, 10, 16))]
)
def test_detail_when_actual_article_is_image_only(index: int, posted: date) -> None:
    # Given
    candidate = parse_list(
        (FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1
    ).candidates[index - 1]
    html = (FIXTURES / f"detail-{index}.html").read_text(encoding="utf-8")
    # When
    result = parse_detail(html, candidate)
    # Then
    assert len(result.image_urls) == 1
    assert result.body_text == ""
    assert result.posted_on == posted
    assert result.release_on is result.is_seasonal is result.is_limited is None
    assert result.thumbnail_url == candidate.thumbnail_url


def test_key_when_same_article_appears_on_another_page() -> None:
    # Given
    urls = [
        "/bbs/detail/?" + b64encode(f"bbs_idx=708&bbs_category=3&bbs_page={p}".encode()).decode()
        for p in (1, 2)
    ]
    # When / Then
    assert post_key(urls[0]) == post_key(urls[1]) == "event:708"


@pytest.mark.parametrize(
    "payload",
    [
        "garbage",
        "bbs_idx=1&bbs_category=1",
        "bbs_idx=x&bbs_category=3",
        "bbs_idx=1&bbs_idx=2&bbs_category=3",
    ],
)
def test_key_when_query_is_invalid_or_wrong_category(payload: str) -> None:
    # Given
    url = "/bbs/detail/?" + b64encode(payload.encode()).decode()
    # When / Then
    with pytest.raises(CollectionError, match="INVALID_URL"):
        _ = post_key(url)


def test_list_when_markup_is_not_the_official_gallery() -> None:
    # Given / When / Then
    with pytest.raises(CollectionError, match="LIST_LAYOUT_CHANGED"):
        _ = parse_list("<html>maintenance</html>", 1)


def test_detail_when_body_is_missing() -> None:
    # Given
    candidate = parse_list(
        (FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1
    ).candidates[0]
    # When / Then
    with pytest.raises(CollectionError, match="DETAIL_LAYOUT_CHANGED"):
        _ = parse_detail('<div class="board_detail"><h1>title</h1></div>', candidate)


def test_adapter_when_wire_pages_supply_gallery_and_image_article() -> None:
    # Given
    requests: list[str] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        name = "detail-1.html" if request.url.path == "/bbs/detail/" else "list-page1.html"
        return httpx2.Response(
            200, content=(FIXTURES / name).read_bytes(), headers={"content-type": "text/html"}
        )

    async def run() -> PostContent:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            adapter = MegaAdapter(HttpFetcher(client, brand="mega"))
            listing = await adapter.list_page(1)
            return await adapter.fetch_detail(listing.candidates[0])

    # When
    result = anyio.run(run)
    # Then
    assert result.source_key == "event:708"
    assert result.title == "[이벤트] 겨울시즌 신메뉴 출시 이벤트"
    assert len(requests) == 2
    assert requests[1].startswith("https://www.mega-mgccoffee.com/bbs/detail/?")


def test_detail_when_date_is_not_published_does_not_infer_from_image_filename() -> None:
    # Given
    candidate = parse_list(
        (FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1
    ).candidates[0]
    html = (
        '<div class="board_detail"><div class="board_detail_title"><h1>새 소식</h1></div>'
        '<div class="board_detail_text">'
        '<img src="https://img.mega-mgccoffee.com/megahp/20261026.jpg"></div></div>'
    )
    # When
    result = parse_detail(html, candidate)
    # Then
    assert result.posted_on is None
