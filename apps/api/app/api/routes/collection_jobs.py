from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.collection_logs import CollectionLogRead
from app.schemas.collection_jobs import CollectionJobCreateResponse, CollectionJobRead
from app.services import collection_jobs as collection_job_service


router = APIRouter(tags=["collection"])


@router.post("/api/projects/{project_id}/collect", response_model=CollectionJobCreateResponse)
def create_collection_job(project_id: UUID, db: DbSession) -> CollectionJobCreateResponse:
    job, log = collection_job_service.create_pending_collection_job(db, project_id)
    return CollectionJobCreateResponse.model_validate(job).model_copy(
        update={"log": CollectionLogRead.model_validate(log)}
    )


@router.get("/api/jobs/{job_id}", response_model=CollectionJobRead)
def get_collection_job(job_id: UUID, db: DbSession) -> CollectionJobRead:
    return CollectionJobRead.model_validate(collection_job_service.get_collection_job(db, job_id))
