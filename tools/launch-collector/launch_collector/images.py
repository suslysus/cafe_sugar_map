"""Optional bounded image download, separate from the database-shaped payload."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

import anyio
from pydantic import HttpUrl

from launch_collector.errors import CollectionError
from launch_collector.models import FrozenModel, SourceKey

if TYPE_CHECKING:
    from launch_collector.batch import BrandBatch
    from launch_collector.network import Fetcher, Resource


class SavedImage(FrozenModel):
    source_url: HttpUrl
    post_keys: tuple[SourceKey, ...]
    path: str
    sha256: str
    byte_count: int


class FailedImage(FrozenModel):
    source_url: HttpUrl
    post_keys: tuple[SourceKey, ...]
    error_code: str


class ImageManifest(FrozenModel):
    downloaded: tuple[SavedImage, ...] = ()
    failed: tuple[FailedImage, ...] = ()


def image_extension(resource: Resource) -> str:
    data = resource.data
    if resource.content_type not in {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/octet-stream",
    }:
        raise CollectionError("INVALID_IMAGE")
    if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n") and b"IEND" in data[-12:]:
        return ".png"
    if data.startswith((b"GIF87a", b"GIF89a")) and data.endswith(b";"):
        return ".gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return ".webp"
    raise CollectionError("INVALID_IMAGE")


async def save_images(batch: BrandBatch, fetcher: Fetcher, directory: Path) -> ImageManifest:
    await anyio.Path(directory).mkdir(parents=True, exist_ok=True)
    references: dict[HttpUrl, list[SourceKey]] = {}
    for post in batch.posts:
        for url in post.image_urls:
            references.setdefault(url, []).append(post.source_key)
    saved: list[SavedImage] = []
    failed: list[FailedImage] = []
    for url, keys in references.items():
        try:
            resource = await fetcher.fetch(url)
            extension = image_extension(resource)
            digest = sha256(resource.data).hexdigest()
            path = anyio.Path(directory) / (digest + extension)
            if await path.exists():
                if sha256(await path.read_bytes()).hexdigest() != digest:
                    failed.append(
                        FailedImage(
                            source_url=url, post_keys=tuple(keys), error_code="IMAGE_FILE_CONFLICT"
                        )
                    )
                    continue
            else:
                _ = await path.write_bytes(resource.data)
            saved.append(
                SavedImage(
                    source_url=url,
                    post_keys=tuple(keys),
                    path=str(await path.resolve()),
                    sha256=digest,
                    byte_count=len(resource.data),
                )
            )
        except CollectionError as error:
            failed.append(FailedImage(source_url=url, post_keys=tuple(keys), error_code=error.code))
        except OSError:
            failed.append(
                FailedImage(source_url=url, post_keys=tuple(keys), error_code="IMAGE_WRITE_FAILED")
            )
    return ImageManifest(downloaded=tuple(saved), failed=tuple(failed))
