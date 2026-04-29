from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import ApiSchema


class CollectionLogRead(ApiSchema):
    id: UUID
    job_id: UUID
    platform: str
    status: str
    items_collected: int = 0
    items_inserted: int = 0
    items_skipped: int = 0
    error_message: str | None = None
    rate_limit_remaining: int | None = None
    rate_limit_reset_at: datetime | None = None
    created_at: datetime
