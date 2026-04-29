from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.db.models import ClusterSignal, Opportunity, RawItem, Signal


HIGH_VALUE_PAIN_LEVEL = 70
HIGH_VALUE_SIGNAL_CONFIDENCE = 60


@dataclass(frozen=True)
class QualityRawItem:
    id: Any
    source_url: str
    platform: str | None = None
    deleted_at_source: bool = False


@dataclass(frozen=True)
class QualitySignal:
    id: Any
    raw_item_id: Any
    signal_type: str | None
    pain_level: int | None
    signal_confidence: int | None
    summary_zh: str | None = None
    recommended_action: str | None = None
    created_at: Any = None


def is_high_value_signal(signal: QualitySignal | Signal, raw_item: QualityRawItem | RawItem | None = None) -> bool:
    if raw_item is not None and bool(getattr(raw_item, "deleted_at_source", False)):
        return False
    if getattr(signal, "signal_type", None) == "noise":
        return False
    pain_level = getattr(signal, "pain_level", None) or 0
    signal_confidence = getattr(signal, "signal_confidence", None) or 0
    return pain_level >= HIGH_VALUE_PAIN_LEVEL and signal_confidence >= HIGH_VALUE_SIGNAL_CONFIDENCE


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def build_signal_quality_summary_from_records(
    *,
    raw_items: list[QualityRawItem],
    signals: list[QualitySignal],
    clustered_signal_ids: set[Any],
    opportunity_count: int,
    llm_json_failure_count: int = 0,
    fallback_classification_count: int = 0,
) -> dict[str, Any]:
    raw_items_by_id = {item.id: item for item in raw_items}
    processed_raw_item_ids = {signal.raw_item_id for signal in signals}
    total_signals = len(signals)

    eligible_signals = [
        signal
        for signal in signals
        if not bool(getattr(raw_items_by_id.get(signal.raw_item_id), "deleted_at_source", False))
    ]
    high_value = [
        signal
        for signal in eligible_signals
        if is_high_value_signal(signal, raw_items_by_id.get(signal.raw_item_id))
    ]
    noise_count = sum(1 for signal in signals if signal.signal_type == "noise")

    top_signals = sorted(
        high_value,
        key=lambda signal: (
            signal.pain_level or 0,
            signal.signal_confidence or 0,
            signal.created_at is not None,
            signal.created_at,
        ),
        reverse=True,
    )[:5]

    top_5_high_value_signals = []
    for signal in top_signals:
        raw_item = raw_items_by_id.get(signal.raw_item_id)
        if raw_item is None or not raw_item.source_url:
            continue
        top_5_high_value_signals.append(
            {
                "signal_id": str(signal.id),
                "raw_item_id": str(signal.raw_item_id),
                "source_url": raw_item.source_url,
                "platform": raw_item.platform,
                "signal_type": signal.signal_type,
                "pain_level": signal.pain_level,
                "signal_confidence": signal.signal_confidence,
                "summary_zh": signal.summary_zh,
                "recommended_action": signal.recommended_action,
            }
        )

    return {
        "total_raw_items": len(raw_items),
        "processed_raw_items": len(processed_raw_item_ids),
        "total_signals": total_signals,
        "high_value_signals": len(high_value),
        "high_value_ratio": _ratio(len(high_value), total_signals),
        "noise_ratio": _ratio(noise_count, total_signals),
        "llm_json_failure_count": llm_json_failure_count,
        "fallback_classification_count": fallback_classification_count,
        "cluster_coverage_rate": _ratio(len(clustered_signal_ids), total_signals),
        "opportunity_count": opportunity_count,
        "top_5_high_value_signals": top_5_high_value_signals,
    }


def build_signal_quality_summary(
    db: Session,
    project_id: UUID,
    *,
    llm_json_failure_count: int = 0,
    fallback_classification_count: int = 0,
) -> dict[str, Any]:
    raw_item_rows = db.execute(
        select(
            RawItem.id,
            RawItem.source_url,
            RawItem.platform,
            RawItem.deleted_at_source,
        ).where(RawItem.project_id == project_id)
    ).all()
    signal_rows = db.execute(
        select(
            Signal.id,
            Signal.raw_item_id,
            Signal.signal_type,
            Signal.pain_level,
            Signal.signal_confidence,
            Signal.summary_zh,
            Signal.recommended_action,
            Signal.created_at,
        ).where(Signal.project_id == project_id)
    ).all()

    signal_ids = [row.id for row in signal_rows]
    if signal_ids:
        clustered_signal_ids = set(
            db.scalars(
                select(distinct(ClusterSignal.signal_id)).where(ClusterSignal.signal_id.in_(signal_ids))
            ).all()
        )
    else:
        clustered_signal_ids = set()

    opportunity_count = int(
        db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.project_id == project_id)) or 0
    )

    return build_signal_quality_summary_from_records(
        raw_items=[
            QualityRawItem(
                id=row.id,
                source_url=row.source_url,
                platform=row.platform,
                deleted_at_source=row.deleted_at_source,
            )
            for row in raw_item_rows
        ],
        signals=[
            QualitySignal(
                id=row.id,
                raw_item_id=row.raw_item_id,
                signal_type=row.signal_type,
                pain_level=row.pain_level,
                signal_confidence=row.signal_confidence,
                summary_zh=row.summary_zh,
                recommended_action=row.recommended_action,
                created_at=row.created_at,
            )
            for row in signal_rows
        ],
        clustered_signal_ids=clustered_signal_ids,
        opportunity_count=opportunity_count,
        llm_json_failure_count=llm_json_failure_count,
        fallback_classification_count=fallback_classification_count,
    )
