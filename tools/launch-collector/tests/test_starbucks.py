from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import parse_qs

import anyio
import httpx2
import pytest

from launch_collector import starbucks
from launch_collector.errors import CollectionError
from launch_collector.network import HttpFetcher

FIXTURES = Path(__file__).parent / "fixtures" / "starbucks"


def test_list_when_actual_two_pages_are_parsed() -> None:
    # Given
    first = (FIXTURES / "list-page-1.json").read_bytes()
    second = (FIXTURES / "list-page-2.json").read_bytes()
    # When
    page1 = starbucks.parse_list(first, 1)
    page2 = starbucks.parse_list(second, 2)
    # Then
    assert len(page1.candidates) == len(page2.candidates) == 10
    assert page1.candidates[0].source_key == "news:6703"
    assert page2.candidates[0].source_key == "news:6584"
    assert page1.next_page == 2
    assert page2.next_page == 3
    assert page1.candidates[0].posted_on == date(2026, 11, 9)
    assert str(page1.candidates[0].thumbnail_url) == (
        "https://image.istarbucks.co.kr/upload/news/RxLCG3_WEB_THUM_20261109094321619.jpg"
    )
    assert str(page1.candidates[0].source_url).endswith("newsView.do?cate=N01&seq=6703")


@pytest.mark.parametrize(
    "payload",
    [
        b"{}",
        b'{"cnt":-1,"list":[]}',
        b'{"cnt":1,"list":[]}',
        b'{"cnt":0,"list":[{}]}',
        b'{"cnt":"0","list":[]}',
        b'{"cnt":1,"list":[{"seq":1,"title":"x","img_nm":"","news_dt":123}]}',
        b'{"cnt":1,"list":[{"seq":"1","title":"x","img_nm":"","news_dt":"2026-11-09"}]}',
    ],
)
def test_list_when_schema_is_changed(payload: bytes) -> None:
    # Given / When / Then
    with pytest.raises(CollectionError, match="LIST_LAYOUT_CHANGED"):
        _ = starbucks.parse_list(payload, 1)


def test_list_when_official_total_is_zero() -> None:
    # Given / When
    page = starbucks.parse_list(b'{"cnt":0,"list":[]}', 1)
    # Then
    assert page.explicit_empty
    assert page.board_recognized
    assert page.next_page is None


@pytest.mark.parametrize(
    "date_field", [b"", b',"news_dt":null', b',"news_dt":""', b',"news_dt":"bad"']
)
def test_list_when_date_is_unknown(date_field: bytes) -> None:
    # Given
    payload = b'{"cnt":1,"list":[{"seq":1,"title":"x","img_nm":""' + date_field + b"}]}"
    # When
    page = starbucks.parse_list(payload, 1)
    # Then
    assert page.candidates[0].posted_on is None


def test_list_when_final_page_has_one_row() -> None:
    # Given
    data = b'{"cnt":11,"list":[{"seq":1,"title":"A &amp; B","img_nm":"","news_dt":"2026-11-09"}]}'
    # When
    page = starbucks.parse_list(data, 2)
    # Then
    assert page.next_page is None
    assert page.candidates[0].title == "A & B"
    assert page.candidates[0].thumbnail_url is None


def test_detail_when_actual_image_article_is_parsed() -> None:
    # Given
    candidate = starbucks.parse_list((FIXTURES / "list-page-1.json").read_bytes(), 1).candidates[0]
    # When
    result = starbucks.parse_detail((FIXTURES / "detail.json").read_bytes(), candidate)
    # Then
    assert len(result.image_urls) == 4
    assert result.image_urls[0].host == "image.istarbucks.co.kr"
    assert "조선델리 노엘 트리 케이크" in result.body_text
    assert "margin" not in result.body_text
    assert result.posted_on == date(2026, 11, 9)
    assert result.release_on is result.is_seasonal is result.is_limited is None


@pytest.mark.parametrize("payload", [b"{}", b'{"view":null}', b'{"view":{"seq":1,"content":"x"}}'])
def test_detail_when_required_content_or_identity_is_invalid(payload: bytes) -> None:
    # Given
    candidate = starbucks.parse_list((FIXTURES / "list-page-1.json").read_bytes(), 1).candidates[0]
    # When / Then
    with pytest.raises(CollectionError, match="DETAIL_LAYOUT_CHANGED"):
        _ = starbucks.parse_detail(payload, candidate)


def test_adapter_when_list_and_detail_are_requested() -> None:
    # Given
    calls: list[tuple[str, dict[str, list[str]]]] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        calls.append((request.url.path, parse_qs(request.content.decode(), keep_blank_values=True)))
        filename = (
            "list-page-2.json" if request.url.path.endswith("newsListAjax.do") else "detail.json"
        )
        return httpx2.Response(200, content=(FIXTURES / filename).read_bytes())

    async def run() -> None:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            adapter = starbucks.StarbucksAdapter(HttpFetcher(client, brand="starbucks"))
            page = await adapter.list_page(2)
            assert page.candidates[0].source_key == "news:6584"
            candidate = starbucks.parse_list(
                (FIXTURES / "list-page-1.json").read_bytes(), 1
            ).candidates[0]
            _ = await adapter.fetch_detail(candidate)

    # When
    anyio.run(run)
    # Then
    assert calls == [
        (
            "/whats_new/newsListAjax.do",
            {"cate": ["N01"], "pageIndex": ["2"], "searchKeyword": [""], "searchKey": ["3"]},
        ),
        ("/whats_new/newsViewAjax.do", {"seq": ["6703"], "view_yn": [""]}),
    ]
