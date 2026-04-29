from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema


class ProjectBase(ApiSchema):
    name: str = Field(min_length=1)
    description: str | None = None
    platforms_enabled: dict[str, bool] | None = None
    collection_frequency: str = "manual"


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ApiSchema):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    platforms_enabled: dict[str, bool] | None = None
    collection_frequency: str | None = None


class ProjectRead(ProjectBase):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectDeleted(ApiSchema):
    id: UUID
    deleted: bool = True
