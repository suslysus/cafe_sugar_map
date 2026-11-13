"""Brand-level storage input and partition checks."""

from __future__ import annotations

from typing import Annotated, Literal, assert_never
from uuid import UUID

from pydantic import BeforeValidator, StrictInt, TypeAdapter, model_validator

from launch_collector.models import (
    BrandId,
    CollectedPost,
    ContractError,
    FailedDetail,
    FrozenModel,
    SeenPost,
    Timestamp,
)

ListStatus = Literal["ok", "partial", "failed"]
BatchStatus = Literal["ok", "partial", "failed"]
SchemaVersion = Annotated[Literal[1], BeforeValidator(TypeAdapter(StrictInt).validate_python)]


class BrandBatch(FrozenModel):
    schema_version: SchemaVersion
    run_id: UUID
    brand_id: BrandId
    attempted_at: Timestamp
    list_status: ListStatus
    seen: tuple[SeenPost, ...]
    posts: tuple[CollectedPost, ...]
    failed_details: tuple[FailedDetail, ...]
    error_code: str | None

    @model_validator(mode="after")
    def check_key_partition(self) -> BrandBatch:
        seen = [item.source_key for item in self.seen]
        posts = [item.source_key for item in self.posts]
        failed = [item.source_key for item in self.failed_details]
        for keys in (seen, posts, failed):
            if len(keys) != len(set(keys)):
                raise ContractError("DUPLICATE_KEY")
        if set(posts) & set(failed) or set(seen) != set(posts) | set(failed):
            raise ContractError("KEY_PARTITION_MISMATCH")
        match self.list_status:
            case "failed":
                if seen or posts or failed:
                    raise ContractError("FAILED_LIST_HAS_DATA")
                if not self.error_code:
                    raise ContractError("FAILED_LIST_MISSING_ERROR")
            case "ok" | "partial":
                pass
            case unreachable:
                assert_never(unreachable)
        return self

    @property
    def status(self) -> BatchStatus:
        if self.failed_details:
            return "partial"
        return self.list_status


class IngestRequest(FrozenModel):
    p_payload: BrandBatch
