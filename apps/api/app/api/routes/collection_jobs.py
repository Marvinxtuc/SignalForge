from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body
from sqlalchemy import select

from app.api.errors import phase_not_available
from app.api.deps import DbSession
from app.db.models import CollectionLog
from app.schemas.collection_logs import CollectionLogRead
from app.schemas.collection_jobs import (
    DEFAULT_EXECUTION_MODE,
    PHASE_4_EXECUTION_MODES,
    PHASE_4_FORBIDDEN_MODE_MESSAGE,
    CollectionJobCreateRequest,
    CollectionJobCreateResponse,
    CollectionJobRead,
)
from app.services.collection_executor import execute_collection
from app.services import collection_jobs as collection_job_service


router = APIRouter(tags=["collection"])


@router.post("/api/projects/{project_id}/collect", response_model=CollectionJobCreateResponse)
def create_collection_job(
    project_id: UUID,
    db: DbSession,
    payload: CollectionJobCreateRequest | None = Body(default=None),
) -> CollectionJobCreateResponse:
    execution_mode = _execution_mode(payload)
    if execution_mode not in PHASE_4_EXECUTION_MODES:
        raise phase_not_available(PHASE_4_FORBIDDEN_MODE_MESSAGE)

    job = execute_collection(db, project_id=project_id, execution_mode=execution_mode)

    log = db.scalar(
        select(CollectionLog)
        .where(CollectionLog.job_id == job.id)
        .order_by(CollectionLog.created_at.desc(), CollectionLog.id.desc())
        .limit(1)
    )
    response = CollectionJobCreateResponse.model_validate(job)
    return response.model_copy(
        update={
            "collector_execution": execution_mode,
            "log": CollectionLogRead.model_validate(log) if log is not None else None,
        }
    )


@router.get("/api/jobs/{job_id}", response_model=CollectionJobRead)
def get_collection_job(job_id: UUID, db: DbSession) -> CollectionJobRead:
    return CollectionJobRead.model_validate(collection_job_service.get_collection_job(db, job_id))


def _execution_mode(payload: CollectionJobCreateRequest | None) -> str:
    if payload is None:
        return DEFAULT_EXECUTION_MODE
    mode = payload.execution_mode
    if not isinstance(mode, str):
        raise phase_not_available(PHASE_4_FORBIDDEN_MODE_MESSAGE)
    normalized = mode.strip()
    return normalized or DEFAULT_EXECUTION_MODE
