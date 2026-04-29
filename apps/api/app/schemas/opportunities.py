from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema


OpportunityStatus = Literal["new", "watching", "validating", "build_candidate", "content_candidate", "archived"]


class OpportunityRead(ApiSchema):
    id: UUID
    project_id: UUID
    cluster_id: UUID | None = None
    title: str
    description: str | None = None
    status: str
    opportunity_score: int | None = None
    evidence_count: int
    platform_distribution: dict[str, Any] | None = None
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OpportunityUpdate(ApiSchema):
    title: str | None = None
    description: str | None = None
    status: OpportunityStatus | None = None
    opportunity_score: int | None = Field(default=None, ge=0, le=100)
    evidence_count: int | None = Field(default=None, ge=0)
    platform_distribution: dict[str, Any] | None = None
    last_seen_at: datetime | None = None
