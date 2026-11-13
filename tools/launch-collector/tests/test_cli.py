from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter

ROOT = Path(__file__).resolve().parents[1]


def test_validate_when_example_payload_is_valid() -> None:
    # Given
    command = [
        sys.executable,
        "-B",
        str(ROOT / "collect.py"),
        "validate",
        str(ROOT / "examples" / "brand-payload.json"),
    ]
    # When
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    # Then
    assert result.returncode == 0, result.stderr
    report = TypeAdapter(dict[str, str | int]).validate_json(result.stdout)
    assert report["brand_id"] == "paik"
    assert report["selected_count"] == report["fetched_count"] == 1
    assert report["failed_count"] == 0
    assert report["auto_accepted_count"] == 0


@pytest.mark.parametrize(
    ("arguments", "expected_code"),
    [
        (["--help"], 0),
        (["collect", "--brand", "paik"], 2),
        (["collect", "--brand", "hollys"], 2),
        (["validate", str(ROOT / "examples" / "missing.json")], 2),
        (["validate", str(ROOT / "pyproject.toml")], 2),
    ],
)
def test_cli_when_command_is_not_collection_success(
    arguments: list[str], expected_code: int
) -> None:
    # Given
    command = [sys.executable, "-B", str(ROOT / "collect.py"), *arguments]
    # When
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False)
    # Then
    assert result.returncode == expected_code
    if expected_code:
        assert not result.stdout
        assert result.stderr
