from __future__ import annotations

from pathlib import Path

import anyio
import httpx2
import pytest
from pydantic import HttpUrl

from launch_collector.batch import IngestRequest
from launch_collector.errors import CollectionError
from launch_collector.images import save_images
from launch_collector.network import HttpFetcher, Resource

EXAMPLE = Path(__file__).parents[1] / "examples" / "brand-payload.json"


def test_network_when_redirect_points_outside_official_host() -> None:
    # Given
    calls: list[str] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        calls.append(str(request.url))
        return httpx2.Response(302, headers={"location": "http://127.0.0.1/private"})

    async def run() -> Resource:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            return await HttpFetcher(client).fetch(HttpUrl("https://paikdabang.com/news/"))

    # When / Then
    with pytest.raises(CollectionError, match="INVALID_URL"):
        _ = anyio.run(run)
    assert calls == ["https://paikdabang.com/news/"]


def test_network_when_response_exceeds_limit() -> None:
    # Given
    def respond(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=b"0123456789")

    async def run() -> Resource:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            return await HttpFetcher(client, max_bytes=5).fetch(
                HttpUrl("https://paikdabang.com/news/")
            )

    # When / Then
    with pytest.raises(CollectionError, match="RESPONSE_TOO_LARGE"):
        _ = anyio.run(run)


def test_images_when_html_is_disguised_as_a_photo(tmp_path: Path) -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    post = batch.posts[0].model_copy(
        update={"image_urls": (HttpUrl("https://paikdabang.com/wp-content/uploads/test.jpg"),)}
    )
    batch = batch.model_copy(update={"posts": (post,)})

    def respond(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200, content=b"<html>not a picture</html>", headers={"content-type": "image/jpeg"}
        )

    async def run() -> tuple[int, tuple[str, ...]]:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(respond)) as client:
            manifest = await save_images(batch, HttpFetcher(client), tmp_path)
            return len(manifest.downloaded), tuple(item.error_code for item in manifest.failed)

    # When
    downloaded, errors = anyio.run(run)
    # Then
    assert downloaded == 0
    assert errors
    assert set(errors) == {"INVALID_IMAGE"}
    assert not list(tmp_path.glob("*.jpg"))
