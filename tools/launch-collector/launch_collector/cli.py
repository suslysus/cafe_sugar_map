"""CLI for checking a proposed storage payload without network or DB access."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Literal, assert_never

from pydantic import ValidationError

from launch_collector.batch import IngestRequest


class CommandArgs(argparse.Namespace):
    """Mutable namespace populated by argparse before command dispatch."""

    def __init__(self) -> None:
        super().__init__()
        self.command: Literal["validate", "collect"] = "collect"
        self.file: Path = Path()


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="공식 소식 수집기: 현재는 입력 형식 검증만 지원합니다."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="JSON 형식·키 일치 검사 (수집/DB 저장 없음)")
    _ = validate.add_argument("file", type=Path)
    collect = commands.add_parser("collect", help="후속 PR에서 구현할 수집 명령 (현재 실행 불가)")
    _ = collect.add_argument(
        "--brand", choices=["all", "starbucks", "mega", "compose", "paik"], default="all"
    )
    args = CommandArgs()
    _ = parser.parse_args(namespace=args)
    match args.command:
        case "validate":
            return validate_file(args.file)
        case "collect":
            print(json.dumps({"error": "COLLECTION_NOT_IMPLEMENTED"}), file=sys.stderr)
            return 2
        case unreachable:
            assert_never(unreachable)
