from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Cluster, ClusterSignal, Embedding, RawItem, Signal
from app.processing.embedding_client import EMBEDDING_DIMENSION, validate_embedding


DEFAULT_SIMILARITY_THRESHOLD = 0.82


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimension")
    if not left:
        raise ValueError("vectors must not be empty")

    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _platform_distribution(db: Session, cluster_id: Any) -> dict[str, int]:
    rows = db.execute(
        select(RawItem.platform)
        .join(Signal, Signal.raw_item_id == RawItem.id)
        .join(ClusterSignal, ClusterSignal.signal_id == Signal.id)
        .where(ClusterSignal.cluster_id == cluster_id)
    ).all()
    distribution: dict[str, int] = {}
    for (platform,) in rows:
        distribution[platform] = distribution.get(platform, 0) + 1
    return distribution


def refresh_cluster_rollups(db: Session, cluster: Cluster) -> Cluster:
    cluster.evidence_count = int(
        db.scalar(
            select(func.count())
            .select_from(ClusterSignal)
            .where(ClusterSignal.cluster_id == cluster.id)
        )
        or 0
    )
    cluster.source_diversity = _platform_distribution(db, cluster.id)
    cluster.last_seen_at = datetime.now(UTC)
    return cluster


def _signal_title(signal: Signal) -> str:
    title = signal.summary_zh or signal.recommended_action or f"Signal cluster {signal.id}"
    title = " ".join(title.split())
    return title[:120] or "Untitled signal cluster"


def _candidate_clusters(db: Session, project_id: Any) -> list[tuple[Cluster, list[float]]]:
    rows = db.execute(
        select(Cluster, Embedding.embedding)
        .join(ClusterSignal, ClusterSignal.cluster_id == Cluster.id)
        .join(Embedding, Embedding.signal_id == ClusterSignal.signal_id)
        .where(Cluster.project_id == project_id)
        .order_by(Cluster.updated_at.desc().nullslast(), Cluster.created_at.desc())
    ).all()

    candidates: dict[Any, tuple[Cluster, list[float]]] = {}
    for cluster, embedding in rows:
        candidates.setdefault(cluster.id, (cluster, list(embedding)))
    return list(candidates.values())


def find_best_cluster(
    db: Session,
    *,
    project_id: Any,
    embedding: list[float],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[Cluster | None, float]:
    validate_embedding(embedding, dimension=EMBEDDING_DIMENSION)
    best_cluster: Cluster | None = None
    best_score = -1.0
    for cluster, cluster_embedding in _candidate_clusters(db, project_id):
        score = cosine_similarity(embedding, cluster_embedding)
        if score > best_score:
            best_cluster = cluster
            best_score = score
    if best_cluster is None or best_score < threshold:
        return None, best_score
    return best_cluster, best_score


def assign_signal_to_cluster(
    db: Session,
    *,
    signal: Signal,
    embedding: list[float],
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> tuple[Cluster, ClusterSignal, bool]:
    cluster, similarity = find_best_cluster(
        db,
        project_id=signal.project_id,
        embedding=embedding,
        threshold=threshold,
    )
    created = False
    if cluster is None:
        created = True
        cluster = Cluster(
            project_id=signal.project_id,
            title=_signal_title(signal),
            description=signal.recommended_action or signal.summary_zh,
            opportunity_score=signal.pain_level,
            status="new",
            source_diversity={},
            evidence_count=0,
            last_seen_at=datetime.now(UTC),
        )
        db.add(cluster)
        db.flush()
        similarity = 1.0

    link = db.scalar(
        select(ClusterSignal).where(
            ClusterSignal.cluster_id == cluster.id,
            ClusterSignal.signal_id == signal.id,
        )
    )
    if link is None:
        link = ClusterSignal(cluster_id=cluster.id, signal_id=signal.id, similarity_score=float(similarity))
        db.add(link)
        db.flush()
    else:
        link.similarity_score = float(similarity)

    cluster.evidence_count = int(
        db.scalar(
            select(func.count())
            .select_from(ClusterSignal)
            .where(ClusterSignal.cluster_id == cluster.id)
        )
        or 0
    )
    cluster.source_diversity = _platform_distribution(db, cluster.id)
    cluster.last_seen_at = datetime.now(UTC)
    return cluster, link, created
