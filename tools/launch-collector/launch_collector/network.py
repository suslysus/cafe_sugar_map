"""Bounded transport restricted to each brand's official site and media hosts."""

from __future__ import annotations

import socket
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal, Protocol

import httpx2

from launch_collector.errors import CollectionError
from launch_collector.urls import brand_url

if TYPE_CHECKING:
    from pydantic import HttpUrl

    from launch_collector.models import BrandId

MAX_RESOURCE_BYTES: Final = 12 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class Resource:
    url: HttpUrl
    data: bytes
    content_type: str

    def html(self) -> str:
        if self.content_type not in {"text/html", "application/xhtml+xml"}:
            raise CollectionError("NOT_HTML")
        try:
            return self.data.decode("utf-8-sig")
        except UnicodeError:
            raise CollectionError("HTML_DECODE_FAILED") from None


class Fetcher(Protocol):
    async def fetch(self, url: HttpUrl) -> Resource: ...


class FormFetcher(Fetcher, Protocol):
    async def post_form(self, url: HttpUrl, data: Mapping[str, str]) -> Resource: ...


def create_client() -> httpx2.AsyncClient:
    transport = httpx2.AsyncHTTPTransport(
        http2=True,
        retries=2,
        limits=httpx2.Limits(max_connections=50, max_keepalive_connections=20, keepalive_expiry=60),
        socket_options=[(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)],
    )
    return httpx2.AsyncClient(
        transport=transport,
        timeout=httpx2.Timeout(connect=5, read=30, write=10, pool=10),
        follow_redirects=True,
        headers={"User-Agent": "CafeSugarMapStudentCollector/0.2"},
    )


@dataclass(frozen=True, slots=True)
class HttpFetcher:
    client: httpx2.AsyncClient
    max_bytes: int = MAX_RESOURCE_BYTES
    brand: BrandId = "paik"

    async def fetch(self, url: HttpUrl) -> Resource:
        return await self.request(url, None)

    async def post_form(self, url: HttpUrl, data: Mapping[str, str]) -> Resource:
        return await self.request(url, data)

    async def request(self, url: HttpUrl, data: Mapping[str, str] | None) -> Resource:
        current = brand_url(str(url), self.brand)
        method: Literal["GET", "POST"] = "GET" if data is None else "POST"
        form = data
        try:
            for _ in range(6):
                # Validate each redirect before making its request, including image redirects.
                async with self.client.stream(
                    method, str(current), data=form, follow_redirects=False
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise CollectionError("INVALID_REDIRECT")
                        current = brand_url(location, self.brand, str(current))
                        if response.status_code == HTTPStatus.SEE_OTHER or (
                            method == "POST"
                            and response.status_code
                            in {HTTPStatus.MOVED_PERMANENTLY, HTTPStatus.FOUND}
                        ):
                            method, form = "GET", None
                        continue
                    if response.status_code != HTTPStatus.OK:
                        code = f"HTTP_{response.status_code}"
                        raise CollectionError(code)
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > self.max_bytes:
                            raise CollectionError("RESPONSE_TOO_LARGE")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0]
                    return Resource(current, bytes(body), content_type.strip().lower())
        except httpx2.HTTPError:
            raise CollectionError("NETWORK_ERROR") from None
        raise CollectionError("TOO_MANY_REDIRECTS")
