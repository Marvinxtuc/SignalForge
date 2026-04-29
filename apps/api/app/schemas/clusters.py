from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema


ClusterStatus = Literal["new", "watching", "validating", "archived"]


class ClusterRead(ApiSchema):
    id: UUID
    project_id: UUID
    title: str
    description: str | None = None
    opportunity_score: int | None = None
    status: str
    source_diversity: dict[str, Any] | None = None
    evidence_count: int
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ClusterUpdate(ApiSchema):
    title: str | None = None
    description: str | None = None
    opportunity_score: int | None = Field(default=None, ge=0, le=100)
    status: ClusterStatus | None = None
    source_diversity: dict[str, Any] | None = None
    evidence_count: int | None = Field(default=None, ge=0)
    last_seen_at: datetime | None = None
