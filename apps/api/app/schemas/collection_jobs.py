from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.collection_logs import CollectionLogRead
from app.schemas.common import ApiSchema


COLLECTOR_NOT_AVAILABLE = "not_available_until_phase_3_or_later"
DEFAULT_EXECUTION_MODE = "safe_disabled"
PHASE_4_EXECUTION_MODES = {
    "mock",
    "disabled_only",
    DEFAULT_EXECUTION_MODE,
    "reddit",
    "product_hunt",
    "p0_real",
}
PHASE_4_FORBIDDEN_MODE_MESSAGE = "Requested connector execution mode is not available in Phase 4."


class CollectionJobCreateRequest(ApiSchema):
    execution_mode: Any = DEFAULT_EXECUTION_MODE


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
