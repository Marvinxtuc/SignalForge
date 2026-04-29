from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import Cluster, Opportunity, Project, RawItem, Signal
from app.schemas.reports import ReportRequest
from app.services.common import get_or_404


def _high_value_signals(db: Session, project_id: UUID, min_pain_level: int) -> list[tuple[Signal, RawItem]]:
    stmt = (
        select(Signal, RawItem)
        .join(RawItem, Signal.raw_item_id == RawItem.id)
        .where(Signal.project_id == project_id)
        .where(Signal.is_need_signal.is_(True))
        .where(Signal.pain_level >= min_pain_level)
        .order_by(desc(Signal.pain_level), Signal.created_at.desc())
    )
    return list(db.execute(stmt).all())


def _top_clusters(db: Session, project_id: UUID, limit: int) -> list[Cluster]:
    stmt = (
        select(Cluster)
        .where(Cluster.project_id == project_id)
        .order_by(desc(Cluster.opportunity_score), desc(Cluster.evidence_count), Cluster.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _opportunities(db: Session, project_id: UUID, limit: int) -> list[Opportunity]:
    stmt = (
        select(Opportunity)
        .where(Opportunity.project_id == project_id)
        .order_by(desc(Opportunity.opportunity_score), desc(Opportunity.evidence_count), Opportunity.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def generate_markdown_report(db: Session, project_id: UUID, request: ReportRequest) -> str:
    project = get_or_404(db, Project, project_id, "Project")
    signals = _high_value_signals(db, project_id, request.min_pain_level)
    clusters = _top_clusters(db, project_id, request.top_clusters_limit)
    opportunities = _opportunities(db, project_id, request.opportunities_limit)

    lines = [
        f"# SignalForge Report: {project.name}",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"High value threshold: pain_level >= {request.min_pain_level}",
        "",
        "## High Value Signals",
    ]

    if not signals:
        lines.append("- No high value signals found.")
    for signal, raw_item in signals:
        lines.append(
            "- "
            f"[{raw_item.platform}] Pain {signal.pain_level}: "
            f"{signal.summary_zh or raw_item.content_excerpt or raw_item.content_text or 'No summary'} "
            f"(source_url: {raw_item.source_url})"
        )

    lines.extend(["", "## Top Clusters"])
    if not clusters:
        lines.append("- No clusters found.")
    for cluster in clusters:
        lines.append(
            "- "
            f"{cluster.title} | score: {cluster.opportunity_score} | "
            f"evidence_count: {cluster.evidence_count}"
        )

    lines.extend(["", "## Opportunities"])
    if not opportunities:
        lines.append("- No opportunities found.")
    for opportunity in opportunities:
        lines.append(
            "- "
            f"{opportunity.title} | status: {opportunity.status} | "
            f"score: {opportunity.opportunity_score} | evidence_count: {opportunity.evidence_count}"
        )

    return "\n".join(lines) + "\n"


def generate_csv_report(db: Session, project_id: UUID, request: ReportRequest) -> str:
    get_or_404(db, Project, project_id, "Project")
    signals = _high_value_signals(db, project_id, request.min_pain_level)

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "signal_id",
            "platform",
            "signal_type",
            "pain_level",
            "summary_zh",
            "source_url",
            "created_at",
        ],
    )
    writer.writeheader()

    for signal, raw_item in signals:
        writer.writerow(
            {
                "signal_id": str(signal.id),
                "platform": raw_item.platform,
                "signal_type": signal.signal_type or "",
                "pain_level": signal.pain_level if signal.pain_level is not None else "",
                "summary_zh": signal.summary_zh or "",
                "source_url": raw_item.source_url,
                "created_at": signal.created_at.isoformat() if signal.created_at else "",
            }
        )

    return buffer.getvalue()
