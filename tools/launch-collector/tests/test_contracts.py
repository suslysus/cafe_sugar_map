from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import HttpUrl, ValidationError

from launch_collector.batch import BrandBatch, IngestRequest

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "brand-payload.json"


def encode(batch: BrandBatch) -> str:
    return '{"p_payload":' + batch.model_dump_json() + "}"


def test_batch_when_detail_fails_but_other_post_is_valid() -> None:
    # Given
    request = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8"))
    batch = request.p_payload.model_copy(update={"list_status": "partial"})
    # When
    parsed = IngestRequest.model_validate_json(encode(batch)).p_payload
    # Then
    assert parsed.status == "partial"
    assert len(parsed.posts) == 1


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('"brand_id": "paik"', '"brand_id": "hollys"'),
        ('"schema_version": 1', '"schema_version": 2'),
        ('"schema_version": 1', '"schema_version": true'),
        ('"auto_decision": "needs_review"', '"auto_decision": "unknown"'),
        ('"release_on": null', '"release_on": "2026-02-30"'),
        ('"is_seasonal": null', '"is_seasonal": "true"'),
        ('"2026-11-09T04:00:00Z"', '"2026-11-09T04:00:00+09:00"'),
        ('"2026-11-09T04:00:00Z"', '"2026-11-09T04:00:00"'),
        ('"https://paikdabang.com/post_news/example-only/"', '"file:///private.txt"'),
    ],
)
def test_contract_when_field_is_invalid(old: str, new: str) -> None:
    # Given
    text = EXAMPLE.read_text(encoding="utf-8")
    assert old in text
    changed = text.replace(old, new)
    # When / Then
    with pytest.raises(ValidationError):
        _ = IngestRequest.model_validate_json(changed)


def test_contract_when_key_appears_twice() -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    changed = batch.model_copy(update={"seen": batch.seen + batch.seen})
    # When / Then
    with pytest.raises(ValidationError, match="DUPLICATE_KEY"):
        _ = IngestRequest.model_validate_json(encode(changed))


def test_contract_when_post_does_not_match_seen_key() -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    changed = batch.model_copy(update={"seen": ()})
    # When / Then
    with pytest.raises(ValidationError, match="KEY_PARTITION_MISMATCH"):
        _ = IngestRequest.model_validate_json(encode(changed))


def test_contract_when_failed_list_has_existing_data() -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    changed = batch.model_copy(update={"list_status": "failed", "error_code": "HTTP_403"})
    # When / Then
    with pytest.raises(ValidationError, match="FAILED_LIST_HAS_DATA"):
        _ = IngestRequest.model_validate_json(encode(changed))


def test_contract_when_board_is_really_empty() -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    changed = batch.model_copy(update={"seen": (), "posts": ()})
    # When
    parsed = IngestRequest.model_validate_json(encode(changed)).p_payload
    # Then
    assert parsed.status == "ok"
    assert not parsed.posts


def test_contract_when_post_is_only_a_poster() -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    post = batch.posts[0].model_copy(
        update={"body_text": "", "image_urls": (HttpUrl("https://example.com/poster.jpg"),)}
    )
    # When
    parsed = IngestRequest.model_validate_json(encode(batch.model_copy(update={"posts": (post,)})))
    # Then
    assert len(parsed.p_payload.posts[0].image_urls) == 1


def test_contract_when_post_has_no_text_or_image() -> None:
    # Given
    batch = IngestRequest.model_validate_json(EXAMPLE.read_text(encoding="utf-8")).p_payload
    post = batch.posts[0].model_copy(update={"body_text": " "})
    # When / Then
    with pytest.raises(ValidationError, match="EMPTY_CONTENT"):
        _ = IngestRequest.model_validate_json(encode(batch.model_copy(update={"posts": (post,)})))
