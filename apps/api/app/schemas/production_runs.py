from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema


class ProductionRunCreate(ApiSchema):
    project_id: UUID | None = None
    collection_mode: str = "mock"
    processing_mode: str = "fallback_only"
    reprocess: bool = False
    allow_real_platform_write: bool = False
    allow_real_llm: bool = False
    allow_real_embedding: bool = False
    execute: bool = True
    rollback_hint: str | None = None
    redacted_logs: list[dict[str, Any]] | None = None


class ProductionRunCloseout(ApiSchema):
    status: str = Field(default="closed", min_length=1)
    result_summary: dict[str, Any] | None = None
    error_summary: str | None = None
    rollback_hint: str | None = None
    redacted_logs: list[dict[str, Any]] | None = None


class ProductionRunRead(ApiSchema):
    id: UUID
    project_id: UUID | None = None
    status: str
    stage: str
    collection_mode: str
    processing_mode: str
    allow_real_platform_write: bool
    allow_real_llm: bool
    allow_real_embedding: bool
    env_preflight: dict[str, Any]
    result_summary: dict[str, Any]
    error_summary: str | None = None
    rollback_hint: str | None = None
    redacted_logs: list[dict[str, Any]]
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
