from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import not_found
from app.db.models import Cluster, Opportunity, Project, RawItem, Signal
from app.schemas.common import PaginationParams
from app.schemas.opportunities import OpportunityUpdate
from app.services.common import commit_and_refresh, get_or_404, paginate, parse_uuid


def list_project_opportunities(
    db: Session,
    project_id: UUID | str,
    pagination: PaginationParams,
) -> tuple[list[Opportunity], int]:
    parsed_project_id = project_id if isinstance(project_id, UUID) else parse_uuid(str(project_id), "project_id")
    get_or_404(db, Project, parsed_project_id, "Project")
    stmt = (
        select(Opportunity)
        .where(Opportunity.project_id == parsed_project_id)
        .order_by(Opportunity.opportunity_score.desc().nullslast(), Opportunity.last_seen_at.desc().nullslast())
    )
    return paginate(db, stmt, pagination)


def get_opportunity(db: Session, opportunity_id: UUID | str) -> Opportunity:
    return get_or_404(db, Opportunity, opportunity_id, "Opportunity")


def create_opportunity_from_signal(db: Session, signal_id: UUID | str) -> Opportunity:
    parsed_signal_id = signal_id if isinstance(signal_id, UUID) else parse_uuid(str(signal_id), "signal_id")
    row = db.execute(
        select(Signal, RawItem)
        .join(RawItem, RawItem.id == Signal.raw_item_id)
        .where(Signal.id == parsed_signal_id)
    ).one_or_none()
    if row is None:
        raise not_found("Signal not found", {"id": str(parsed_signal_id)})

    signal, raw_item = row
    title = signal.summary_zh or signal.recommended_action or raw_item.content_excerpt or "Signal-derived opportunity"
    if len(title) > 120:
        title = f"{title[:117]}..."
    opportunity = Opportunity(
        project_id=signal.project_id,
        cluster_id=None,
        title=title,
        description=signal.recommended_action or signal.summary_zh,
        status="new",
        opportunity_score=signal.pain_level,
        evidence_count=1,
        platform_distribution={raw_item.platform: 1},
        last_seen_at=signal.created_at,
    )
    db.add(opportunity)
    return commit_and_refresh(db, opportunity)


def create_opportunity_from_cluster(db: Session, cluster_id: UUID | str) -> Opportunity:
    cluster = get_or_404(db, Cluster, cluster_id, "Cluster")
    opportunity = Opportunity(
        project_id=cluster.project_id,
        cluster_id=cluster.id,
        title=cluster.title,
        description=cluster.description,
        status="new",
        opportunity_score=cluster.opportunity_score,
        evidence_count=cluster.evidence_count,
        platform_distribution=cluster.source_diversity,
        last_seen_at=cluster.last_seen_at,
    )
    db.add(opportunity)
    return commit_and_refresh(db, opportunity)


def update_opportunity(db: Session, opportunity_id: UUID | str, payload: OpportunityUpdate) -> Opportunity:
    opportunity = get_opportunity(db, opportunity_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(opportunity, field, value)
    return commit_and_refresh(db, opportunity)


def archive_opportunity(db: Session, opportunity_id: UUID | str) -> Opportunity:
    opportunity = get_opportunity(db, opportunity_id)
    opportunity.status = "archived"
    return commit_and_refresh(db, opportunity)
