from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import CollectionLog


def create_collection_log(
    db: Session,
    *,
    job_id: UUID,
    platform: str,
    status: str,
    items_collected: int = 0,
    items_inserted: int = 0,
    items_skipped: int = 0,
    error_message: str | None = None,
    rate_limit_remaining: int | None = None,
    rate_limit_reset_at: datetime | None = None,
) -> CollectionLog:
    log = CollectionLog(
        job_id=job_id,
        platform=platform,
        status=status,
        items_collected=items_collected,
        items_inserted=items_inserted,
        items_skipped=items_skipped,
        error_message=error_message,
        rate_limit_remaining=rate_limit_remaining,
        rate_limit_reset_at=rate_limit_reset_at,
    )
    db.add(log)
    db.flush()
    return log
