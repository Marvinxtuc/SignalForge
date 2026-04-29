from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class ApiSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorEnvelope(BaseModel):
    error: dict[str, object]


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(ApiSchema, Generic[T]):
    items: list[T]
    page: int = 1
    page_size: int = 20
    total: int = 0


class IdResponse(ApiSchema):
    id: UUID


class TimestampedSchema(ApiSchema):
    created_at: datetime | None = None
    updated_at: datetime | None = None

