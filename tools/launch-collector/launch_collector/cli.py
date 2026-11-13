"""Validate payloads or collect official posts to explicitly selected local paths."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal, assert_never

import anyio
from pydantic import ValidationError

from launch_collector import network
from launch_collector.batch import IngestRequest
from launch_collector.collecting import CollectionLimits, collect_brand
from launch_collector.compose import ComposeAdapter
from launch_collector.images import ImageManifest, save_images
from launch_collector.mega import MegaAdapter
from launch_collector.paik import PaikAdapter
from launch_collector.starbucks import StarbucksAdapter

if TYPE_CHECKING:
    from launch_collector.adapters import BrandAdapter
    from launch_collector.models import BrandId
    from launch_collector.network import FormFetcher


class CommandArgs(argparse.Namespace):
    """Mutable namespace populated by argparse before command dispatch."""

    def __init__(self) -> None:
        super().__init__()
        self.command: Literal["validate", "collect"] = "collect"
        self.file: Path = Path()
        self.brand: Literal["all", "starbucks", "mega", "compose", "paik"] = "all"
        self.output: Path = Path()
        self.image_dir: Path | None = None
        self.max_posts: int = 10
        self.max_pages: int = 3


def validate_file(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        logging.getLogger(__name__).warning("INPUT_READ_FAILED")
        return 2
    try:
        batch = IngestRequest.model_validate_json(text).p_payload
    except ValidationError as error:
        issues = [
            {"path": ".".join(map(str, issue["loc"])), "type": issue["type"]}
            for issue in error.errors(include_input=False, include_context=False, include_url=False)
        ]
        print(json.dumps({"error": "INVALID_PAYLOAD", "issues": issues}), file=sys.stderr)
        return 2
    report = {
        "brand_id": batch.brand_id,
        "status": batch.status,
        "selected_count": len(batch.seen),
        "fetched_count": len(batch.posts),
        "failed_count": len(batch.failed_details),
        "auto_accepted_count": sum(post.auto_decision == "accepted" for post in batch.posts),
    }
    print(json.dumps(report, ensure_ascii=False))
    return 0


def adapter_for(brand: BrandId, fetcher: FormFetcher) -> BrandAdapter:
    match brand:
        case "paik":
            return PaikAdapter(fetcher)
        case "mega":
            return MegaAdapter(fetcher)
        case "compose":
            return ComposeAdapter(fetcher)
        case "starbucks":
            return StarbucksAdapter(fetcher)
        case unreachable:
            assert_never(unreachable)


async def run_collection(args: CommandArgs, limits: CollectionLimits, brand: BrandId) -> int:
    manifest = ImageManifest()
    try:
        async with network.create_client() as client:
            fetcher = network.HttpFetcher(client, brand=brand)
            result = await collect_brand(adapter_for(brand, fetcher), limits)
            await anyio.Path(args.output.parent).mkdir(parents=True, exist_ok=True)
            _ = await anyio.Path(args.output).write_text(
                result.request.model_dump_json(indent=2), encoding="utf-8"
            )
            if args.image_dir is not None:
                manifest = await save_images(result.request.p_payload, fetcher, args.image_dir)
                _ = await anyio.Path(args.image_dir / "image-manifest.json").write_text(
                    manifest.model_dump_json(indent=2), encoding="utf-8"
                )
    except OSError:
        logging.getLogger(__name__).warning("OUTPUT_WRITE_FAILED")
        return 2
    batch = result.request.p_payload
    print(
        json.dumps(
            {
                "brand_id": batch.brand_id,
                "status": batch.status,
                "selected_count": len(batch.seen),
                "fetched_count": len(batch.posts),
                "failed_count": len(batch.failed_details),
                "pages_read": result.pages_read,
                "has_more": result.has_more,
                "accepted_count": sum(post.auto_decision == "accepted" for post in batch.posts),
                "needs_review_count": sum(
                    post.auto_decision == "needs_review" for post in batch.posts
                ),
                "excluded_count": sum(post.auto_decision == "excluded" for post in batch.posts),
                "image_download_requested": args.image_dir is not None,
                "images_downloaded": len(manifest.downloaded),
                "images_failed": len(manifest.failed),
                "error_code": batch.error_code,
            },
            ensure_ascii=False,
        )
    )
    match batch.status:
        case "failed":
            return 2
        case "partial":
            return 1
        case "ok":
            return 1 if manifest.failed else 0
        case unreachable:
            assert_never(unreachable)


def collect_command(args: CommandArgs) -> int:
    match args.brand:
        case ("paik" | "mega" | "compose" | "starbucks") as brand:
            try:
                limits = CollectionLimits(max_posts=args.max_posts, max_pages=args.max_pages)
            except ValidationError:
                print(json.dumps({"error": "INVALID_COLLECTION_LIMITS"}), file=sys.stderr)
                return 2
            try:
                if args.image_dir is not None and args.output.resolve() in {
                    args.image_dir.resolve(),
                    (args.image_dir / "image-manifest.json").resolve(),
                }:
                    print(json.dumps({"error": "INVALID_OUTPUT_PATHS"}), file=sys.stderr)
                    return 2
            except OSError:
                print(json.dumps({"error": "INVALID_OUTPUT_PATHS"}), file=sys.stderr)
                return 2
            return anyio.run(run_collection, args, limits, brand)
        case "all":
            print(json.dumps({"error": "BRAND_NOT_IMPLEMENTED"}), file=sys.stderr)
            return 2
        case unreachable:
            assert_never(unreachable)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="공식 소식 수집기: 입력 검증과 네 브랜드 로컬 수집 (DB 저장 없음)"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="JSON 형식·키 일치 검사 (수집/DB 저장 없음)")
    _ = validate.add_argument("file", type=Path)
    collect = commands.add_parser("collect", help="공식 브랜드 게시글을 로컬 JSON으로 수집")
    _ = collect.add_argument(
        "--brand", choices=["all", "starbucks", "mega", "compose", "paik"], default="all"
    )
    _ = collect.add_argument("--output", type=Path, required=True, help="로컬 payload JSON 경로")
    _ = collect.add_argument("--image-dir", type=Path, help="실제 사진·manifest 저장 폴더 (선택)")
    _ = collect.add_argument("--max-posts", type=int, default=10, help="서로 다른 글 수: 1~200")
    _ = collect.add_argument("--max-pages", type=int, default=3, help="목록 페이지 수: 1~20")
    args = CommandArgs()
    _ = parser.parse_args(namespace=args)
    match args.command:
        case "validate":
            return validate_file(args.file)
        case "collect":
            return collect_command(args)
        case unreachable:
            assert_never(unreachable)
