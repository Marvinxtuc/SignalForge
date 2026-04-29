from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Cluster, ClusterSignal, Opportunity, RawItem, Signal


def clamp_score(value: float | int | None) -> int:
    if value is None:
        return 0
    return max(0, min(100, int(round(float(value)))))


def calculate_opportunity_score(
    *,
    pain_level_avg: float,
    frequency_score: float,
    source_diversity_score: float,
    clarity_score_avg: float,
    freshness_score: float,
    engagement_score: float,
) -> int:
    score = (
        pain_level_avg * 0.30
        + frequency_score * 0.25
        + source_diversity_score * 0.15
        + clarity_score_avg * 0.15
        + freshness_score * 0.10
        + engagement_score * 0.05
    )
    return clamp_score(score)


def _cluster_signal_rows(db: Session, cluster: Cluster) -> list[tuple[Signal, RawItem]]:
    return list(
        db.execute(
            select(Signal, RawItem)
            .join(ClusterSignal, ClusterSignal.signal_id == Signal.id)
            .join(RawItem, RawItem.id == Signal.raw_item_id)
            .where(ClusterSignal.cluster_id == cluster.id)
        ).all()
    )


def _engagement_score(rows: list[tuple[Signal, RawItem]]) -> int:
    total = 0
    for _, raw_item in rows:
        engagement = raw_item.engagement or {}
        for key in ("score", "comments", "votes", "reactions"):
            value = engagement.get(key)
            if isinstance(value, int | float):
                total += int(value)
    return clamp_score(min(100, total))


def summarize_cluster_for_opportunity(db: Session, cluster: Cluster) -> dict[str, Any]:
    rows = _cluster_signal_rows(db, cluster)
    signal_count = max(len(rows), 1)
    pain_level_avg = sum((signal.pain_level or 0) for signal, _ in rows) / signal_count
    clarity_score_avg = sum((signal.clarity_score or 0) for signal, _ in rows) / signal_count
    platform_distribution: dict[str, int] = {}
    for _, raw_item in rows:
        platform_distribution[raw_item.platform] = platform_distribution.get(raw_item.platform, 0) + 1

    frequency_score = clamp_score(len(rows) * 20)
    source_diversity_score = clamp_score(len(platform_distribution) * 35)
    freshness_score = 80 if rows else 0
    engagement_score = _engagement_score(rows)
    opportunity_score = calculate_opportunity_score(
        pain_level_avg=pain_level_avg,
        frequency_score=frequency_score,
        source_diversity_score=source_diversity_score,
        clarity_score_avg=clarity_score_avg,
        freshness_score=freshness_score,
        engagement_score=engagement_score,
    )

    return {
        "opportunity_score": opportunity_score,
        "evidence_count": len(rows),
        "platform_distribution": platform_distribution,
        "last_seen_at": datetime.now(UTC),
    }


def upsert_opportunity_from_cluster(db: Session, cluster: Cluster) -> Opportunity:
    summary = summarize_cluster_for_opportunity(db, cluster)
    opportunity = db.scalar(select(Opportunity).where(Opportunity.cluster_id == cluster.id))
    if opportunity is None:
        opportunity = Opportunity(
            project_id=cluster.project_id,
            cluster_id=cluster.id,
            title=cluster.title,
            description=cluster.description,
            status="new",
        )
        db.add(opportunity)
        db.flush()

    # Preserve human-maintained fields: status/title/description, especially archived.
    opportunity.opportunity_score = summary["opportunity_score"]
    opportunity.evidence_count = summary["evidence_count"]
    opportunity.platform_distribution = summary["platform_distribution"]
    opportunity.last_seen_at = summary["last_seen_at"]
    cluster.opportunity_score = summary["opportunity_score"]
    cluster.evidence_count = summary["evidence_count"]
    cluster.source_diversity = summary["platform_distribution"]
    cluster.last_seen_at = summary["last_seen_at"]
    return opportunity
