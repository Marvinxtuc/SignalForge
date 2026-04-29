from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession, PaginationDep
from app.schemas.collection_logs import CollectionLogRead
from app.schemas.common import PaginatedResponse
from app.services import collection_jobs as collection_job_service


router = APIRouter(tags=["collection"])


@router.get("/api/projects/{project_id}/collection-logs", response_model=PaginatedResponse[CollectionLogRead])
def list_collection_logs(
    project_id: UUID,
    pagination: PaginationDep,
    db: DbSession,
) -> PaginatedResponse[CollectionLogRead]:
    logs, total = collection_job_service.list_collection_logs_for_project(db, project_id, pagination)
    return PaginatedResponse[CollectionLogRead](
        items=[CollectionLogRead.model_validate(log) for log in logs],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
