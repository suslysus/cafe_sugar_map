from __future__ import annotations

from collections.abc import Mapping

import anyio
import httpx2
import pytest
from pydantic import HttpUrl

from launch_collector import urls
from launch_collector.errors import CollectionError
from launch_collector.network import HttpFetcher, Resource


def test_brand_url_when_other_brand_host_is_supplied() -> None:
    # Given / When / Then
    with pytest.raises(CollectionError, match="INVALID_URL"):
        _ = urls.brand_url("https://paikdabang.com/news/", "compose")


def test_brand_url_when_official_media_is_relative_or_absolute() -> None:
    # Given / When
    relative = urls.brand_url("/files/a.jpg", "compose")
    cdn = urls.brand_url("//image.istarbucks.co.kr/upload/news/a.jpg", "starbucks")
    # Then
    assert str(relative) == "https://composecoffee.com/files/a.jpg"
    assert str(cdn) == "https://image.istarbucks.co.kr/upload/news/a.jpg"


@pytest.mark.parametrize("target", ["http://127.0.0.1/a", "https://evil.test/a"])
def test_brand_transport_when_form_redirect_leaves_official_hosts(target: str) -> None:
    # Given
    calls: list[tuple[str, str]] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        calls.append((request.method, str(request.url)))
        return httpx2.Response(307, headers={"location": target})

    async def run() -> Resource:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            fetcher = HttpFetcher(client, brand="starbucks")
            data: Mapping[str, str] = {"cate": "N01", "pageIndex": "2"}
            return await fetcher.post_form(
                HttpUrl("https://www.starbucks.co.kr/whats_new/newsListAjax.do"), data
            )

    # When / Then
    with pytest.raises(CollectionError, match="INVALID_URL"):
        _ = anyio.run(run)
    assert len(calls) == 1


def test_brand_transport_when_posting_read_only_news_query() -> None:
    # Given
    bodies: list[bytes] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        bodies.append(request.content)
        return httpx2.Response(200, json={"cnt": 0, "list": []})

    async def run() -> Resource:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            return await HttpFetcher(client, brand="starbucks").post_form(
                HttpUrl("https://www.starbucks.co.kr/whats_new/newsListAjax.do"),
                {"cate": "N01", "pageIndex": "2"},
            )

    # When
    result = anyio.run(run)
    # Then
    assert result.data == b'{"cnt":0,"list":[]}'
    assert bodies == [b"cate=N01&pageIndex=2"]
