from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession, PaginationDep
from app.schemas.common import PaginatedResponse
from app.schemas.opportunities import OpportunityRead, OpportunityUpdate
from app.services import opportunities as opportunity_service


router = APIRouter(tags=["opportunities"])


@router.get("/api/projects/{project_id}/opportunities", response_model=PaginatedResponse[OpportunityRead])
def list_project_opportunities(
    project_id: UUID,
    db: DbSession,
    pagination: PaginationDep,
) -> PaginatedResponse[OpportunityRead]:
    items, total = opportunity_service.list_project_opportunities(db, project_id, pagination)
    return PaginatedResponse[OpportunityRead](
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/api/opportunities/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: UUID, db: DbSession) -> OpportunityRead:
    return opportunity_service.get_opportunity(db, opportunity_id)


@router.post("/api/signals/{signal_id}/create-opportunity", response_model=OpportunityRead)
def create_opportunity_from_signal(signal_id: UUID, db: DbSession) -> OpportunityRead:
    return opportunity_service.create_opportunity_from_signal(db, signal_id)


@router.post("/api/clusters/{cluster_id}/create-opportunity", response_model=OpportunityRead)
def create_opportunity_from_cluster(cluster_id: UUID, db: DbSession) -> OpportunityRead:
    return opportunity_service.create_opportunity_from_cluster(db, cluster_id)


@router.put("/api/opportunities/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(opportunity_id: UUID, payload: OpportunityUpdate, db: DbSession) -> OpportunityRead:
    return opportunity_service.update_opportunity(db, opportunity_id, payload)


@router.post("/api/opportunities/{opportunity_id}/archive", response_model=OpportunityRead)
def archive_opportunity(opportunity_id: UUID, db: DbSession) -> OpportunityRead:
    return opportunity_service.archive_opportunity(db, opportunity_id)
