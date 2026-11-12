from __future__ import annotations

import base64
import sys
from pathlib import Path

import httpx2
import pytest

from launch_collector import cli, network
from launch_collector.batch import IngestRequest

FIXTURES = Path(__file__).parent / "fixtures" / "paik"
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j6xkAAAAASUVORK5CYII="
)


def test_cli_when_official_wire_responses_include_multiple_posters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Given
    def respond(request: httpx2.Request) -> httpx2.Response:
        if request.url.path.startswith("/wp-content/uploads/"):
            return httpx2.Response(200, content=PNG, headers={"content-type": "image/png"})
        file = "list-page1.html" if request.url.path == "/news/" else "detail-1.html"
        return httpx2.Response(
            200,
            text=(FIXTURES / file).read_text(encoding="utf-8"),
            headers={"content-type": "text/html; charset=utf-8"},
        )

    def client() -> httpx2.AsyncClient:
        return httpx2.AsyncClient(transport=httpx2.MockTransport(respond))

    monkeypatch.setattr(network, "create_client", client)
    output = tmp_path / "payload.json"
    image_dir = tmp_path / "images"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "collect.py",
            "collect",
            "--brand",
            "paik",
            "--max-posts",
            "3",
            "--output",
            str(output),
            "--image-dir",
            str(image_dir),
        ],
    )
    # When
    result = cli.main()
    # Then
    assert result == 0
    batch = IngestRequest.model_validate_json(output.read_text(encoding="utf-8")).p_payload
    assert len(batch.posts) == 3
    assert len({post.source_key for post in batch.posts}) == 3
    assert (image_dir / "image-manifest.json").is_file()
    images = list(image_dir.glob("*.png"))
    assert len(images) == 1
    assert images[0].read_bytes() == PNG


def test_cli_when_brand_has_no_implemented_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Given
    output = tmp_path / "payload.json"
    monkeypatch.setattr(
        sys, "argv", ["collect.py", "collect", "--brand", "all", "--output", str(output)]
    )
    # When
    result = cli.main()
    # Then
    assert result == 2
    assert "BRAND_NOT_IMPLEMENTED" in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize("leaf", ["image-manifest.json", "."])
def test_cli_when_output_paths_conflict_fails_before_network(
    leaf: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    image_dir = tmp_path / "images"
    output = image_dir / leaf

    def no_network() -> httpx2.AsyncClient:
        pytest.fail("Conflicting destinations must be rejected before network access")

    monkeypatch.setattr(network, "create_client", no_network)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "collect.py",
            "collect",
            "--brand",
            "paik",
            "--output",
            str(output),
            "--image-dir",
            str(image_dir),
        ],
    )
    # When
    result = cli.main()
    # Then
    assert result == 2
    assert "INVALID_OUTPUT_PATHS" in capsys.readouterr().err
    assert not output.exists()
    assert not image_dir.exists()
