from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.collection_logs import CollectionLogRead
from app.schemas.common import ApiSchema


COLLECTOR_NOT_AVAILABLE = "not_available_until_phase_3_or_later"


class CollectionJobRead(ApiSchema):
    id: UUID
    project_id: UUID
    status: str
    trigger_type: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_summary: str | None = None
    created_at: datetime


class CollectionJobCreateResponse(CollectionJobRead):
    collector_execution: str = COLLECTOR_NOT_AVAILABLE
    log: CollectionLogRead | None = None
