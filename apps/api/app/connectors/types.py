from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ConnectorStatus(StrEnum):
    SUCCESS = "success"
    DISABLED = "disabled"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    PERMISSION_LIMITED = "permission_limited"


class RateLimitState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    remaining: int | None = Field(default=None, ge=0)
    reset_at: datetime | None = None
    retry_after_seconds: int | None = Field(default=None, ge=0)


class NormalizedRawItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: NonEmptyStr
    platform_item_id: NonEmptyStr
    source_url: NonEmptyStr
    author_hash: str | None = None
    content_text: str | None = None
    content_excerpt: str | None = None
    normalized_text: str | None = None
    language: str | None = None
    engagement: dict[str, Any] | None = None
    keyword_hits: list[str] = Field(default_factory=list)
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    deleted_at_source: bool = False
    created_at_source: datetime | None = None
    collected_at: datetime | None = None


class ConnectorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: NonEmptyStr
    status: ConnectorStatus
    items: list[NormalizedRawItem] = Field(default_factory=list)
    items_collected: int = Field(default=0, ge=0)
    items_inserted: int = Field(default=0, ge=0)
    items_skipped: int = Field(default=0, ge=0)
    error_message: str | None = None
    rate_limit_state: RateLimitState | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectCollectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    platform: NonEmptyStr
    keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    max_items: int | None = Field(default=None, ge=1)
