"""Typed release-post input contracts, independent of HTTP and storage."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Annotated, ClassVar, Literal, NewType

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    JsonValue,
    StringConstraints,
    model_validator,
)

BrandId = Literal["starbucks", "mega", "compose", "paik"]
Decision = Literal["accepted", "needs_review", "excluded"]
SourceKey = NewType("SourceKey", str)
PostKey = Annotated[SourceKey, Field(pattern=r"^[^\s:]+:[^\s]+$")]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ContentHash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
IssueCode = Literal[
    "UTC_REQUIRED",
    "EMPTY_CONTENT",
    "DUPLICATE_KEY",
    "KEY_PARTITION_MISMATCH",
    "FAILED_LIST_HAS_DATA",
    "FAILED_LIST_MISSING_ERROR",
]


class ContractError(ValueError):
    """A validation issue code without copying source data into the error."""

    def __init__(self, code: IssueCode) -> None:
        self.code: IssueCode = code
        super().__init__(code)


def require_utc(value: datetime) -> datetime:
    if value.utcoffset() != timedelta(0):
        raise ContractError("UTC_REQUIRED")
    return value


Timestamp = Annotated[AwareDatetime, AfterValidator(require_utc)]


class FrozenModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", strict=True)


class SeenPost(FrozenModel):
    source_key: PostKey
    observed_at: Timestamp


class FailedDetail(FrozenModel):
    source_key: PostKey
    attempted_at: Timestamp
    error_code: Annotated[str, Field(min_length=1, max_length=80)]


class PostContent(FrozenModel):
    """Official article fields before classification; dates are never inferred."""

    source_key: PostKey
    source_url: HttpUrl
    title: Title
    body_text: str
    image_urls: tuple[HttpUrl, ...]
    thumbnail_url: HttpUrl | None
    posted_on: date | None
    release_on: date | None
    is_seasonal: bool | None
    is_limited: bool | None
    notice_period_text: str | None
    observed_at: Timestamp

    @model_validator(mode="after")
    def require_content(self) -> PostContent:
        if not self.body_text.strip() and not self.image_urls:
            raise ContractError("EMPTY_CONTENT")
        return self


class CollectedPost(PostContent):
    auto_decision: Decision
    evidence: dict[str, JsonValue]
    content_hash: ContentHash
