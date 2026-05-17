from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Cluster, ClusterSignal, Embedding, Project, RawItem, Signal
from app.processing import prepare_text_for_processing
from app.processing.classifier import classify_text
from app.processing.clustering import assign_signal_to_cluster
from app.processing.embedding_client import (
    EmbeddingProviderError,
    MockEmbeddingClient,
    OpenAICompatibleEmbeddingClient,
    validate_embedding,
)
from app.processing.opportunity_scoring import upsert_opportunity_from_cluster
from app.processing.signal_quality import build_signal_quality_summary
from app.processing.types import ClassificationResult, ProcessingCounters, clamp_score
from app.services.common import get_or_404


HIGH_VALUE_PAIN_LEVEL = 70
HIGH_VALUE_CONFIDENCE = 60
SUPPORTED_PROCESSING_MODES = {"mock", "fallback_only", "real_llm_classification", "real_embedding"}


def _raw_items_for_project(db: Session, project_id: UUID) -> list[RawItem]:
    return list(
        db.scalars(
            select(RawItem)
            .where(RawItem.project_id == project_id)
            .order_by(RawItem.collected_at.asc(), RawItem.id.asc())
        )
    )


def _existing_signal(db: Session, raw_item_id: UUID) -> Signal | None:
    return db.scalar(select(Signal).where(Signal.raw_item_id == raw_item_id))


def _classification_for_raw_item(
    raw_item: RawItem,
    safe_text: str,
    *,
    mode: str,
    force_invalid_llm_json: bool,
) -> ClassificationResult:
    if raw_item.deleted_at_source:
        return ClassificationResult(
            is_need_signal=False,
            signal_type="noise",
            pain_level=0,
            clarity_score=20,
            urgency_score=0,
            business_relevance=0,
            model_confidence=90,
            signal_confidence=20,
            summary_zh="Source item was deleted or removed; content ignored.",
            recommended_action="Do not use deleted source content as opportunity evidence.",
            counters=ProcessingCounters(fallback_classification_count=1),
            metadata={"classification_source": "deleted_source_guard"},
        )

    if force_invalid_llm_json:
        return classify_text(
            safe_text,
            mode="mock",
            llm_payload='{"signal_type":"complaint","pain_level":999}',
        )
    return classify_text(safe_text, mode=mode)


def _upsert_signal(db: Session, raw_item: RawItem, classification: ClassificationResult) -> Signal:
    signal = _existing_signal(db, raw_item.id)
    if signal is None:
        signal = Signal(raw_item_id=raw_item.id, project_id=raw_item.project_id, status="new")
        db.add(signal)

    signal.is_need_signal = classification.is_need_signal
    signal.signal_type = classification.signal_type
    signal.pain_level = clamp_score(classification.pain_level)
    signal.clarity_score = clamp_score(classification.clarity_score)
    signal.urgency_score = clamp_score(classification.urgency_score)
    signal.business_relevance = clamp_score(classification.business_relevance)
    signal.model_confidence = clamp_score(classification.model_confidence)
    signal.signal_confidence = clamp_score(classification.signal_confidence)
    signal.summary_zh = classification.summary_zh
    signal.recommended_action = classification.recommended_action
    if raw_item.deleted_at_source:
        signal.status = "ignored"
    elif signal.status is None:
        signal.status = "new"
    db.flush()
    return signal


def _upsert_embedding(db: Session, signal: Signal, vector: list[float], *, model_name: str) -> Embedding:
    validate_embedding(vector)
    embedding = db.scalar(select(Embedding).where(Embedding.signal_id == signal.id))
    if embedding is None:
        embedding = Embedding(signal_id=signal.id, model_name=model_name, embedding=vector)
        db.add(embedding)
    else:
        embedding.embedding = vector
        embedding.model_name = model_name
    db.flush()
    return embedding


def _project_counts(db: Session, project_id: UUID) -> dict[str, int]:
    total_signals = int(db.scalar(select(func.count()).select_from(Signal).where(Signal.project_id == project_id)) or 0)
    embedding_count = int(
        db.scalar(
            select(func.count())
            .select_from(Embedding)
            .join(Signal, Signal.id == Embedding.signal_id)
            .where(Signal.project_id == project_id)
        )
        or 0
    )
    cluster_count = int(db.scalar(select(func.count()).select_from(Cluster).where(Cluster.project_id == project_id)) or 0)
    cluster_signal_count = int(
        db.scalar(
            select(func.count())
            .select_from(ClusterSignal)
            .join(Signal, Signal.id == ClusterSignal.signal_id)
            .where(Signal.project_id == project_id)
        )
        or 0
    )
    high_value_count = int(
        db.scalar(
            select(func.count())
            .select_from(Signal)
            .join(RawItem, RawItem.id == Signal.raw_item_id)
            .where(Signal.project_id == project_id)
            .where(Signal.pain_level >= HIGH_VALUE_PAIN_LEVEL)
            .where(Signal.signal_confidence >= HIGH_VALUE_CONFIDENCE)
            .where(Signal.signal_type != "noise")
            .where(RawItem.deleted_at_source.is_(False))
        )
        or 0
    )
    return {
        "total_signals": total_signals,
        "embedding_count": embedding_count,
        "cluster_count": cluster_count,
        "cluster_signal_count": cluster_signal_count,
        "high_value_signals": high_value_count,
    }


def signal_quality_summary(
    db: Session,
    project_id: UUID,
    *,
    llm_json_failure_count: int = 0,
    fallback_classification_count: int = 0,
) -> dict[str, Any]:
    summary = build_signal_quality_summary(
        db,
        project_id,
        llm_json_failure_count=llm_json_failure_count,
        fallback_classification_count=fallback_classification_count,
    )
    summary.update(
        {
            "embedding_count": _project_counts(db, project_id)["embedding_count"],
            "cluster_count": _project_counts(db, project_id)["cluster_count"],
        }
    )
    return summary


def process_project_raw_items(
    db: Session,
    project_id: UUID,
    mode: str = "mock",
    reprocess: bool = False,
    force_invalid_llm_json: bool = False,
) -> dict[str, Any]:
    if mode not in SUPPORTED_PROCESSING_MODES:
        raise ValueError("Processing pipeline only supports mock, fallback_only, real_llm_classification, and real_embedding modes.")

    get_or_404(db, Project, project_id, "Project")
    raw_items = _raw_items_for_project(db, project_id)
    embedding_client = OpenAICompatibleEmbeddingClient.from_env() if mode == "real_embedding" else MockEmbeddingClient()
    classification_mode = "fallback_only" if mode == "real_embedding" else mode

    processed_in_run = 0
    skipped_existing = 0
    skipped_deleted = 0
    fallback_count = 0
    llm_failures = 0

    try:
        for raw_item in raw_items:
            existing = _existing_signal(db, raw_item.id)
            if existing is not None and not reprocess:
                skipped_existing += 1
                continue

            source_text = raw_item.normalized_text or raw_item.content_text or raw_item.content_excerpt or ""
            prepared = prepare_text_for_processing(source_text)
            classification = _classification_for_raw_item(
                raw_item,
                prepared.redacted_text,
                mode=classification_mode,
                force_invalid_llm_json=force_invalid_llm_json,
            )
            fallback_count += classification.counters.fallback_classification_count
            llm_failures += classification.counters.llm_json_failure_count

            signal = _upsert_signal(db, raw_item, classification)
            if raw_item.deleted_at_source:
                skipped_deleted += 1
                processed_in_run += 1
                continue

            embedding_result = embedding_client.embed_text(prepared.redacted_text)
            vector = embedding_result.embedding
            if mode == "real_embedding":
                try:
                    validate_embedding(vector)
                except ValueError as exc:
                    raise EmbeddingProviderError(str(exc)) from exc
            _upsert_embedding(db, signal, vector, model_name=embedding_result.model_name)
            cluster, _, _ = assign_signal_to_cluster(db, signal=signal, embedding=vector)
            upsert_opportunity_from_cluster(db, cluster)
            processed_in_run += 1

        db.commit()
    except Exception:
        db.rollback()
        raise

    summary = signal_quality_summary(
        db,
        project_id,
        llm_json_failure_count=llm_failures,
        fallback_classification_count=fallback_count,
    )
    summary["processed_in_run"] = processed_in_run
    summary["skipped_existing"] = skipped_existing
    summary["skipped_deleted"] = skipped_deleted
    summary["mode"] = mode
    summary["reprocess"] = reprocess
    return summary
