#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from inspect import signature
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session


ROOT = Path(__file__).resolve().parents[1]
API_ROOT_CANDIDATES = (ROOT, ROOT / "apps" / "api", Path("/app"))
for candidate in API_ROOT_CANDIDATES:
    if (candidate / "app").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


TOKEN_ENV_KEYS = (
    "LLM_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "EMBEDDING_API_KEY",
    "REDDIT_CLIENT_SECRET",
    "PRODUCT_HUNT_TOKEN",
    "SIGNALFORGE_ALLOW_REAL_LLM_SMOKE",
    "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE",
)


class ValidationFailure(Exception):
    pass


def _fail(message: str) -> None:
    raise ValidationFailure(message)


def _pass(message: str) -> None:
    print(f"PASS: {message}")


def _without_real_provider_env() -> dict[str, str | None]:
    original = {key: os.environ.get(key) for key in TOKEN_ENV_KEYS}
    for key in TOKEN_ENV_KEYS:
        os.environ.pop(key, None)
    return original


def _restore_env(original: dict[str, str | None]) -> None:
    for key, value in original.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _load_pipeline_entrypoints() -> tuple[Any, Any]:
    try:
        from app.services.processing_pipeline import get_processing_summary, process_project
    except Exception as exc:  # pragma: no cover - integration guard
        _fail(f"processing pipeline service is not available: {exc}")
    return process_project, get_processing_summary


def _create_raw_only_project(db: Session) -> UUID:
    from app.db.models import (
        Cluster,
        ClusterSignal,
        Embedding,
        Opportunity,
        Project,
        RawItem,
        Signal,
    )

    existing_ids = db.scalars(
        select(Project.id).where(Project.name.like("Phase 5 Processing Validation%"))
    ).all()
    if existing_ids:
        db.execute(delete(ClusterSignal).where(ClusterSignal.cluster_id.in_(select(Cluster.id).where(Cluster.project_id.in_(existing_ids)))))
        db.execute(delete(Embedding).where(Embedding.signal_id.in_(select(Signal.id).where(Signal.project_id.in_(existing_ids)))))
        db.execute(delete(Opportunity).where(Opportunity.project_id.in_(existing_ids)))
        db.execute(delete(Cluster).where(Cluster.project_id.in_(existing_ids)))
        db.execute(delete(Signal).where(Signal.project_id.in_(existing_ids)))
        db.execute(delete(RawItem).where(RawItem.project_id.in_(existing_ids)))
        db.execute(delete(Project).where(Project.id.in_(existing_ids)))
        db.commit()

    project = Project(
        name=f"Phase 5 Processing Validation {datetime.now(UTC).isoformat()}",
        description="Isolated raw-only project for validate_processing_pipeline.py",
        platforms_enabled={"mock": True},
        collection_frequency="manual",
    )
    db.add(project)
    db.flush()

    examples = [
        (
            "validation-need-alerts",
            "I need better alerts when prediction market odds move quickly.",
            ["alerts"],
            {"score": 25, "comments": 12},
        ),
        (
            "validation-expensive-tools",
            "Looking for an alternative to expensive crypto analytics tools.",
            ["alternative"],
            {"score": 19, "comments": 8},
        ),
        (
            "validation-too-noisy",
            "Discord alpha groups are too noisy. I need summaries with source links.",
            ["summaries"],
            {"score": 31, "comments": 14},
        ),
        (
            "validation-unsafe-wallet",
            "This wallet integration feels unsafe and confusing for new users.",
            ["wallet"],
            {"score": 17, "comments": 5},
        ),
        (
            "validation-missing-workflow",
            "I wish there was a tool to track my positions across markets.",
            ["tracking"],
            {"score": 22, "comments": 9},
        ),
        (
            "validation-noise-giveaway",
            "Giveaway referral airdrop hiring now.",
            ["giveaway"],
            {"score": 1, "comments": 0},
        ),
        (
            "validation-deleted",
            "",
            [],
            {"score": 0, "comments": 0},
        ),
    ]
    for platform_item_id, content, keyword_hits, engagement in examples:
        db.add(
            RawItem(
                project_id=project.id,
                platform="mock",
                platform_item_id=platform_item_id,
                source_url=f"https://example.com/phase5/{platform_item_id}",
                author_hash="phase5-demo-author",
                content_text=content,
                content_excerpt=content[:160],
                normalized_text=content.lower() if content else "",
                language="en",
                engagement=engagement,
                keyword_hits=keyword_hits,
                raw_payload={"validation": True},
                deleted_at_source=(platform_item_id == "validation-deleted"),
                created_at_source=datetime.now(UTC),
            )
        )
    db.commit()

    counts = _count_project_objects(db, project.id)
    if counts["raw_items"] < 5:
        _fail(f"isolated validation project has insufficient raw_items: {counts}")
    if any(counts[name] for name in ("signals", "embeddings", "clusters", "opportunities")):
        _fail(f"isolated validation project is not raw-only before processing: {counts}")
    _pass("isolated raw-only validation project created")
    return project.id


def _count_project_objects(db: Session, project_id: UUID) -> dict[str, int]:
    from app.db.models import Cluster, Embedding, Opportunity, RawItem, Signal

    return {
        "raw_items": int(db.scalar(select(func.count()).select_from(RawItem).where(RawItem.project_id == project_id)) or 0),
        "signals": int(db.scalar(select(func.count()).select_from(Signal).where(Signal.project_id == project_id)) or 0),
        "embeddings": int(
            db.scalar(
                select(func.count())
                .select_from(Embedding)
                .join(Signal, Signal.id == Embedding.signal_id)
                .where(Signal.project_id == project_id)
            )
            or 0
        ),
        "clusters": int(db.scalar(select(func.count()).select_from(Cluster).where(Cluster.project_id == project_id)) or 0),
        "opportunities": int(
            db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.project_id == project_id)) or 0
        ),
    }


def _extract_summary(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        if isinstance(value.get("signal_quality"), dict):
            return value["signal_quality"]
        if isinstance(value.get("quality_summary"), dict):
            return value["quality_summary"]
        if isinstance(value.get("processing_summary"), dict):
            return value["processing_summary"]
        return value
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped.get("signal_quality"), dict):
            return dumped["signal_quality"]
        if isinstance(dumped.get("quality_summary"), dict):
            return dumped["quality_summary"]
        if isinstance(dumped.get("processing_summary"), dict):
            return dumped["processing_summary"]
        return dumped
    if hasattr(value, "__dict__"):
        data = dict(value.__dict__)
        if isinstance(data.get("signal_quality"), dict):
            return data["signal_quality"]
        if isinstance(data.get("quality_summary"), dict):
            return data["quality_summary"]
        if isinstance(data.get("processing_summary"), dict):
            return data["processing_summary"]
        return data
    _fail(f"unable to extract processing summary from {type(value)!r}")


def _validate_summary(summary: dict[str, Any]) -> None:
    required = {
        "total_raw_items",
        "processed_raw_items",
        "total_signals",
        "high_value_signals",
        "high_value_ratio",
        "noise_ratio",
        "llm_json_failure_count",
        "fallback_classification_count",
        "cluster_coverage_rate",
        "opportunity_count",
        "top_5_high_value_signals",
    }
    missing = sorted(required - set(summary))
    if missing:
        _fail(f"Signal Quality Gate summary missing fields: {missing}")
    if summary["high_value_signals"] < 2:
        _fail(f"expected at least 2 high value signals: {summary}")
    if summary["processed_raw_items"] < 5:
        _fail(f"expected at least 5 processed raw_items: {summary}")
    if summary["opportunity_count"] < 1:
        _fail(f"expected opportunities to be created or updated: {summary}")
    top_signals = summary["top_5_high_value_signals"]
    if not top_signals:
        _fail(f"expected top_5_high_value_signals: {summary}")
    for item in top_signals:
        if not item.get("source_url"):
            _fail(f"top high value signal lost source_url: {item}")
        if item.get("signal_type") == "noise":
            _fail(f"noise signal appeared in top high value signals: {item}")
    _pass("Signal Quality Gate summary is complete")


def _validate_database_side_effects(db: Session, project_id: UUID) -> None:
    counts = _count_project_objects(db, project_id)
    if counts["signals"] < 5:
        _fail(f"expected signals to be generated from raw_items: {counts}")
    if counts["embeddings"] < counts["signals"] - 1:
        _fail(f"expected embeddings for processed non-deleted signals: {counts}")
    if counts["clusters"] < 1:
        _fail(f"expected clusters to be generated: {counts}")
    if counts["opportunities"] < 1:
        _fail(f"expected opportunities to be generated: {counts}")
    _pass("raw_items -> signals -> embeddings -> clusters -> opportunities verified")


def _validate_idempotency(before: dict[str, int], after: dict[str, int]) -> None:
    for key in ("signals", "embeddings", "clusters", "opportunities"):
        if after[key] != before[key]:
            _fail(f"processing is not idempotent for {key}: before={before}, after={after}")
    _pass("repeated process is idempotent within Phase 5 tolerance")


def _call_process_project(process_project: Any, db: Session, project_id: UUID, **kwargs: Any) -> Any:
    accepted = set(signature(process_project).parameters)
    call_kwargs = {key: value for key, value in kwargs.items() if key in accepted}
    missing_required = [key for key in kwargs if key not in accepted and key.startswith("force_")]
    if missing_required:
        _fail(f"processing pipeline does not expose validation hook(s): {missing_required}")
    return process_project(db, project_id, **call_kwargs)


def validate() -> None:
    from app.db.session import SessionLocal

    if SessionLocal is None:
        _fail("DATABASE_URL is not configured")

    process_project, get_processing_summary = _load_pipeline_entrypoints()
    original_env = _without_real_provider_env()
    try:
        with SessionLocal() as db:
            project_id = _create_raw_only_project(db)

            result = _call_process_project(process_project, db, project_id, mode="mock", reprocess=False)
            if hasattr(result, "model_dump"):
                result_payload = result.model_dump()
            elif isinstance(result, dict):
                result_payload = result
            else:
                result_payload = getattr(result, "__dict__", {})
            if result_payload.get("status") not in {None, "success", "partial_success"}:
                _fail(f"processing pipeline returned unexpected status: {result_payload}")
            db.commit()
            _pass("process mock completed")

            _validate_database_side_effects(db, project_id)
            summary = _extract_summary(get_processing_summary(db, project_id))
            _validate_summary(summary)

            fallback_result = _call_process_project(process_project, db, project_id, mode="fallback_only", reprocess=True)
            fallback_summary = _extract_summary(fallback_result)
            if fallback_summary.get("fallback_classification_count", 0) < 1:
                _fail(f"fallback path was not counted: {fallback_summary}")
            _pass("fallback processing path is counted and does not crash")

            invalid_result = _call_process_project(
                process_project,
                db,
                project_id,
                mode="mock",
                reprocess=True,
                force_invalid_llm_json=True,
            )
            invalid_summary = _extract_summary(invalid_result)
            if invalid_summary.get("llm_json_failure_count", 0) < 1:
                _fail(f"LLM JSON failure path was not counted: {invalid_summary}")
            if invalid_summary.get("fallback_classification_count", 0) < 1:
                _fail(f"LLM JSON failure did not use fallback: {invalid_summary}")
            _pass("LLM JSON failure falls back without crashing")

            before_counts = _count_project_objects(db, project_id)
            _call_process_project(process_project, db, project_id, mode="mock", reprocess=False)
            db.commit()
            after_counts = _count_project_objects(db, project_id)
            _validate_idempotency(before_counts, after_counts)

    finally:
        _restore_env(original_env)

    _pass("no real LLM, embedding, or platform token is required")


def main() -> int:
    try:
        validate()
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    except Exception as exc:
        print(f"FAIL: unexpected validation error: {exc}")
        return 1
    print("PASS: Phase 5 processing pipeline validation complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
