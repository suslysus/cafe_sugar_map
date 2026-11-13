from __future__ import annotations

from datetime import date
from pathlib import Path

import anyio
import httpx2
import pytest

from launch_collector import compose
from launch_collector.errors import CollectionError
from launch_collector.network import HttpFetcher

FIXTURES = Path(__file__).parent / "fixtures" / "compose"


def test_list_when_real_official_pages_have_separate_posts() -> None:
    # Given
    html = (FIXTURES / "list-page1.html").read_text(encoding="utf-8")
    # When
    result = compose.parse_list(html, 1)
    # Then
    assert len(result.candidates) == 20
    assert result.candidates[0].source_key == "news:347839"
    assert str(result.candidates[0].source_url) == "https://composecoffee.com/news/347839"
    assert result.candidates[0].posted_on == date(2026, 10, 29)
    assert result.candidates[0].thumbnail_url is not None
    assert result.next_page == 2


def test_list_when_real_second_page_is_parsed() -> None:
    # Given
    html = (FIXTURES / "list-page2.html").read_text(encoding="utf-8")
    # When
    result = compose.parse_list(html, 2)
    # Then
    assert len(result.candidates) == 20
    assert result.candidates[0].source_key == "news:308703"
    assert result.next_page == 3


@pytest.mark.parametrize("post_id", ["347839", "346088", "338053"])
def test_detail_when_real_official_article_has_text_and_photo(post_id: str) -> None:
    # Given
    listing = compose.parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    candidate = next(item for item in listing.candidates if item.source_key == f"news:{post_id}")
    html = (FIXTURES / f"detail-{post_id}.html").read_text(encoding="utf-8")
    # When
    result = compose.parse_detail(html, candidate)
    # Then
    assert result.title == candidate.title
    assert result.body_text.strip()
    assert result.image_urls
    assert all(url.host == "composecoffee.com" for url in result.image_urls)
    assert result.posted_on == candidate.posted_on
    assert result.release_on is result.is_seasonal is result.is_limited is None


@pytest.mark.parametrize(
    "html",
    [
        "<html>maintenance</html>",
        '<div id="board_list"><ul class="webzine_h"></ul></div>',
        '<div id="board_list"><ul class="webzine_h"><li>broken</li></ul></div>',
    ],
)
def test_list_when_layout_is_unknown_or_row_is_malformed(html: str) -> None:
    # Given / When / Then
    with pytest.raises(CollectionError, match="LIST_LAYOUT_CHANGED"):
        _ = compose.parse_list(html, 1)


def test_list_when_board_explicitly_has_no_posts() -> None:
    # Given
    html = '<div id="board_list"><p class="no_documents">등록된 글이 없습니다.</p></div>'
    # When
    result = compose.parse_list(html, 1)
    # Then
    assert result.explicit_empty
    assert result.candidates == ()


def test_list_when_document_url_contains_paging_and_tracking() -> None:
    # Given
    html = (FIXTURES / "list-page1.html").read_text(encoding="utf-8")
    html = html.replace(
        "https://composecoffee.com/news/347839", "/news/347839?page=2&amp;utm_source=x"
    )
    # When
    result = compose.parse_list(html, 1)
    # Then
    assert str(result.candidates[0].source_url) == "https://composecoffee.com/news/347839"
    assert result.candidates[0].source_key == "news:347839"


def test_detail_when_article_layout_is_missing() -> None:
    # Given
    candidate = compose.parse_list(
        (FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1
    ).candidates[0]
    # When / Then
    with pytest.raises(CollectionError, match="DETAIL_LAYOUT_CHANGED"):
        _ = compose.parse_detail('<div class="read_body">unrelated</div>', candidate)


def test_adapter_when_http_resources_use_real_fixture_markup() -> None:
    # Given
    requests: list[str] = []
    listing = compose.parse_list((FIXTURES / "list-page1.html").read_text(encoding="utf-8"), 1)
    candidate = next(item for item in listing.candidates if item.source_key == "news:338053")

    def serve(request: httpx2.Request) -> httpx2.Response:
        requests.append(str(request.url))
        filename = "list-page2.html" if request.url.path == "/news" else "detail-338053.html"
        return httpx2.Response(
            200,
            text=(FIXTURES / filename).read_text(encoding="utf-8"),
            headers={"content-type": "text/html"},
        )

    async def scenario() -> None:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(serve)) as client:
            adapter = compose.ComposeAdapter(HttpFetcher(client, brand="compose"))
            # When
            result = await adapter.list_page(2)
            article = await adapter.fetch_detail(candidate)
            # Then
            assert adapter.brand_id == "compose"
            assert len(result.candidates) == 20
            assert article.image_urls

    anyio.run(scenario)
    assert requests == [
        "https://composecoffee.com/news?page=2",
        "https://composecoffee.com/news/338053",
    ]
