from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Cluster, Project
from app.schemas.clusters import ClusterUpdate
from app.schemas.common import PaginationParams
from app.services.common import commit_and_refresh, get_or_404, paginate, parse_uuid


def list_project_clusters(
    db: Session,
    project_id: UUID | str,
    pagination: PaginationParams,
) -> tuple[list[Cluster], int]:
    parsed_project_id = project_id if isinstance(project_id, UUID) else parse_uuid(str(project_id), "project_id")
    get_or_404(db, Project, parsed_project_id, "Project")
    stmt = (
        select(Cluster)
        .where(Cluster.project_id == parsed_project_id)
        .order_by(Cluster.opportunity_score.desc().nullslast(), Cluster.last_seen_at.desc().nullslast())
    )
    return paginate(db, stmt, pagination)


def get_cluster(db: Session, cluster_id: UUID | str) -> Cluster:
    return get_or_404(db, Cluster, cluster_id, "Cluster")


def update_cluster(db: Session, cluster_id: UUID | str, payload: ClusterUpdate) -> Cluster:
    cluster = get_cluster(db, cluster_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cluster, field, value)
    return commit_and_refresh(db, cluster)


def archive_cluster(db: Session, cluster_id: UUID | str) -> Cluster:
    cluster = get_cluster(db, cluster_id)
    cluster.status = "archived"
    return commit_and_refresh(db, cluster)
