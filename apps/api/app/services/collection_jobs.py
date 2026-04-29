from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import conflict
from app.db.models import CollectionJob, CollectionLog, Project
from app.schemas.collection_jobs import COLLECTOR_NOT_AVAILABLE
from app.schemas.common import PaginationParams
from app.services.common import get_or_404, paginate


PHASE_2_LOG_MESSAGE = (
    "Phase 2 Backend API created a pending collection job only. "
    "Connector execution is not available until Phase 3 or later."
)


def create_pending_collection_job(db: Session, project_id: UUID) -> tuple[CollectionJob, CollectionLog]:
    get_or_404(db, Project, project_id, "Project")

    job = CollectionJob(project_id=project_id, status="pending", trigger_type="manual")
    log = CollectionLog(
        job_id=job.id,
        platform="system",
        status="pending",
        items_collected=0,
        items_inserted=0,
        items_skipped=0,
        error_message=f"{PHASE_2_LOG_MESSAGE} collector_execution={COLLECTOR_NOT_AVAILABLE}",
    )

    try:
        db.add(job)
        db.flush()
        log.job_id = job.id
        db.add(log)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Unable to create collection job") from exc

    db.refresh(job)
    db.refresh(log)
    return job, log


def get_collection_job(db: Session, job_id: UUID) -> CollectionJob:
    return get_or_404(db, CollectionJob, job_id, "Collection job")


def list_collection_logs_for_project(
    db: Session,
    project_id: UUID,
    pagination: PaginationParams,
) -> tuple[list[CollectionLog], int]:
    get_or_404(db, Project, project_id, "Project")
    stmt = (
        select(CollectionLog)
        .join(CollectionJob, CollectionLog.job_id == CollectionJob.id)
        .where(CollectionJob.project_id == project_id)
        .order_by(CollectionLog.created_at.desc(), CollectionLog.id.desc())
    )
    return paginate(db, stmt, pagination)
