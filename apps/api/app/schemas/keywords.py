from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiSchema


KeywordType = Literal["main", "related", "exclude"]


class KeywordBase(ApiSchema):
    keyword: str = Field(min_length=1)
    keyword_type: KeywordType
    language: str = "all"
    enabled: bool = True


class KeywordCreate(KeywordBase):
    pass


class KeywordUpdate(ApiSchema):
    keyword: str | None = Field(default=None, min_length=1)
    keyword_type: KeywordType | None = None
    language: str | None = None
    enabled: bool | None = None


class KeywordRead(KeywordBase):
    id: UUID
    project_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KeywordDeleted(ApiSchema):
    id: UUID
    deleted: bool = True
