from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import DbSession, PaginationDep
from app.schemas.common import PaginatedResponse
from app.schemas.signals import SignalFeedbackUpdate, SignalRead, SignalStatusUpdate
from app.services import signals as signal_service


router = APIRouter(tags=["signals"])


@router.get("/api/projects/{project_id}/signals", response_model=PaginatedResponse[SignalRead])
def list_project_signals(
    project_id: UUID,
    db: DbSession,
    pagination: PaginationDep,
    platform: str | None = None,
    signal_type: str | None = None,
    min_pain_level: int | None = Query(default=None, ge=0, le=100),
    keyword: str | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> PaginatedResponse[SignalRead]:
    items, total = signal_service.list_project_signals(
        db=db,
        project_id=project_id,
        pagination=pagination,
        platform=platform,
        signal_type=signal_type,
        min_pain_level=min_pain_level,
        keyword=keyword,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )
    return PaginatedResponse[SignalRead](
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/api/signals/{signal_id}", response_model=SignalRead)
def get_signal(signal_id: UUID, db: DbSession) -> SignalRead:
    return signal_service.get_signal(db, signal_id)


@router.put("/api/signals/{signal_id}/feedback", response_model=SignalRead)
def update_signal_feedback(signal_id: UUID, payload: SignalFeedbackUpdate, db: DbSession) -> SignalRead:
    return signal_service.update_signal_feedback(db, signal_id, payload.user_feedback)


@router.put("/api/signals/{signal_id}/status", response_model=SignalRead)
def update_signal_status(signal_id: UUID, payload: SignalStatusUpdate, db: DbSession) -> SignalRead:
    return signal_service.update_signal_status(db, signal_id, payload.status)
