from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession, PaginationDep
from app.schemas.clusters import ClusterRead, ClusterUpdate
from app.schemas.common import PaginatedResponse
from app.services import clusters as cluster_service


router = APIRouter(tags=["clusters"])


@router.get("/api/projects/{project_id}/clusters", response_model=PaginatedResponse[ClusterRead])
def list_project_clusters(
    project_id: UUID,
    db: DbSession,
    pagination: PaginationDep,
) -> PaginatedResponse[ClusterRead]:
    items, total = cluster_service.list_project_clusters(db, project_id, pagination)
    return PaginatedResponse[ClusterRead](
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/api/clusters/{cluster_id}", response_model=ClusterRead)
def get_cluster(cluster_id: UUID, db: DbSession) -> ClusterRead:
    return cluster_service.get_cluster(db, cluster_id)


@router.put("/api/clusters/{cluster_id}", response_model=ClusterRead)
def update_cluster(cluster_id: UUID, payload: ClusterUpdate, db: DbSession) -> ClusterRead:
    return cluster_service.update_cluster(db, cluster_id, payload)


@router.post("/api/clusters/{cluster_id}/archive", response_model=ClusterRead)
def archive_cluster(cluster_id: UUID, db: DbSession) -> ClusterRead:
    return cluster_service.archive_cluster(db, cluster_id)
