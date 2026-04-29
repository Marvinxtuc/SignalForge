from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.api.errors import not_found
from app.db.models import Project, RawItem, Signal
from app.schemas.common import PaginationParams
from app.schemas.signals import SignalRead
from app.services.common import commit_and_refresh, get_or_404, parse_uuid


def _signal_read(signal: Signal, raw_item: RawItem) -> SignalRead:
    return SignalRead(
        id=signal.id,
        raw_item_id=signal.raw_item_id,
        project_id=signal.project_id,
        is_need_signal=signal.is_need_signal,
        signal_type=signal.signal_type,
        pain_level=signal.pain_level,
        clarity_score=signal.clarity_score,
        urgency_score=signal.urgency_score,
        business_relevance=signal.business_relevance,
        model_confidence=signal.model_confidence,
        signal_confidence=signal.signal_confidence,
        summary_zh=signal.summary_zh,
        recommended_action=signal.recommended_action,
        user_feedback=signal.user_feedback,
        status=signal.status,
        created_at=signal.created_at,
        updated_at=signal.updated_at,
        platform=raw_item.platform,
        source_url=raw_item.source_url,
        content_excerpt=raw_item.content_excerpt,
        keyword_hits=raw_item.keyword_hits,
        engagement=raw_item.engagement,
        created_at_source=raw_item.created_at_source,
    )


def _count_rows(db: Session, stmt: Select[tuple[Signal, RawItem]]) -> int:
    total_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    return int(db.scalar(total_stmt) or 0)


def list_project_signals(
    db: Session,
    project_id: UUID | str,
    pagination: PaginationParams,
    platform: str | None = None,
    signal_type: str | None = None,
    min_pain_level: int | None = None,
    keyword: str | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[SignalRead], int]:
    parsed_project_id = project_id if isinstance(project_id, UUID) else parse_uuid(str(project_id), "project_id")
    get_or_404(db, Project, parsed_project_id, "Project")

    stmt: Select[tuple[Signal, RawItem]] = (
        select(Signal, RawItem)
        .join(RawItem, RawItem.id == Signal.raw_item_id)
        .where(Signal.project_id == parsed_project_id)
        .order_by(Signal.pain_level.desc().nullslast(), Signal.created_at.desc())
    )
    if platform:
        stmt = stmt.where(RawItem.platform == platform)
    if signal_type:
        stmt = stmt.where(Signal.signal_type == signal_type)
    if min_pain_level is not None:
        stmt = stmt.where(Signal.pain_level >= min_pain_level)
    if status:
        stmt = stmt.where(Signal.status == status)
    if date_from:
        stmt = stmt.where(Signal.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Signal.created_at <= date_to)
    if keyword:
        keyword_like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                RawItem.normalized_text.ilike(keyword_like),
                RawItem.content_text.ilike(keyword_like),
                RawItem.keyword_hits.any(keyword),
            )
        )

    total = _count_rows(db, stmt)
    rows = db.execute(stmt.offset(pagination.offset).limit(pagination.page_size)).all()
    return [_signal_read(signal, raw_item) for signal, raw_item in rows], total


def get_signal(db: Session, signal_id: UUID | str) -> SignalRead:
    parsed_signal_id = signal_id if isinstance(signal_id, UUID) else parse_uuid(str(signal_id), "signal_id")
    row = db.execute(
        select(Signal, RawItem)
        .join(RawItem, RawItem.id == Signal.raw_item_id)
        .where(Signal.id == parsed_signal_id)
    ).one_or_none()
    if row is None:
        raise not_found("Signal not found", {"id": str(parsed_signal_id)})
    signal, raw_item = row
    return _signal_read(signal, raw_item)


def update_signal_feedback(db: Session, signal_id: UUID | str, user_feedback: str) -> SignalRead:
    signal = get_or_404(db, Signal, signal_id, "Signal")
    signal.user_feedback = user_feedback
    commit_and_refresh(db, signal)
    return get_signal(db, signal.id)


def update_signal_status(db: Session, signal_id: UUID | str, status: str) -> SignalRead:
    signal = get_or_404(db, Signal, signal_id, "Signal")
    signal.status = status
    commit_and_refresh(db, signal)
    return get_signal(db, signal.id)
