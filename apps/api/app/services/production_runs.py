from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.auth import env_flag_enabled
from app.connectors.credential_resolver import PRODUCT_HUNT_ENV_VARS, REAL_PLATFORM_SMOKE_ENV, REDDIT_ENV_VARS
from app.db.models import CollectionLog, ProductionLifecycleRun, Project
from app.processing.llm_client import REQUIRED_LLM_ENV
from app.schemas.common import PaginationParams
from app.schemas.production_runs import ProductionRunCloseout, ProductionRunCreate
from app.services import processing_pipeline
from app.services.collection_executor import execute_collection
from app.services.common import commit_and_refresh, get_or_404, paginate


SAFE_COLLECTION_MODES = {"mock", "disabled_only", "safe_disabled"}
SAFE_PROCESSING_MODES = {"mock", "fallback_only"}
SENSITIVE_KEY_PARTS = ("token", "secret", "password", "credential", "authorization", "cookie", "key")
REDACTED = "[REDACTED]"


def list_runs(db: Session, pagination: PaginationParams) -> tuple[list[ProductionLifecycleRun], int]:
    stmt = select(ProductionLifecycleRun).order_by(
        ProductionLifecycleRun.created_at.desc(),
        ProductionLifecycleRun.id.desc(),
    )
    return paginate(db, stmt, pagination)


def get_run(db: Session, run_id: UUID | str) -> ProductionLifecycleRun:
    return get_or_404(db, ProductionLifecycleRun, run_id, "Production lifecycle run")


def create_run(db: Session, payload: ProductionRunCreate) -> ProductionLifecycleRun:
    if payload.project_id is not None:
        get_or_404(db, Project, payload.project_id, "Project")

    preflight = _preflight(payload)
    lifecycle = [_lifecycle_event("preflight", "pass" if preflight["safe_execution"] else "no_go")]
    now = datetime.now(UTC)
    run = ProductionLifecycleRun(
        project_id=payload.project_id,
        status="running",
        stage="preflight",
        collection_mode=payload.collection_mode,
        processing_mode=payload.processing_mode,
        allow_real_platform_write=payload.allow_real_platform_write,
        allow_real_llm=payload.allow_real_llm,
        allow_real_embedding=payload.allow_real_embedding,
        env_preflight=preflight,
        result_summary={"lifecycle": lifecycle},
        rollback_hint=_redact(payload.rollback_hint),
        redacted_logs=_redact(payload.redacted_logs or []),
        started_at=now,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    if preflight["safe_execution"] is not True:
        run.status = "no_go_real_provider"
        run.stage = "preflight"
        run.error_summary = "Real provider mode blocked by missing approval or environment flags."
        run.result_summary = _redact({"lifecycle": lifecycle})
        run.finished_at = datetime.now(UTC)
        return commit_and_refresh(db, run)

    if payload.project_id is None:
        run.status = "preflight_only"
        run.stage = "preflight"
        run.result_summary = _redact({"lifecycle": lifecycle})
        run.finished_at = datetime.now(UTC)
        return commit_and_refresh(db, run)

    if not payload.execute:
        run.status = "preflight_passed"
        run.stage = "preflight"
        run.result_summary = _redact({"lifecycle": lifecycle})
        run.finished_at = datetime.now(UTC)
        return commit_and_refresh(db, run)

    try:
        lifecycle.append(_lifecycle_event("collect", "running"))
        run.stage = "collect"
        collection_job = execute_collection(
            db,
            project_id=payload.project_id,
            execution_mode=payload.collection_mode,
        )
        collection_log = db.scalar(
            select(CollectionLog)
            .where(CollectionLog.job_id == collection_job.id)
            .order_by(CollectionLog.created_at.desc(), CollectionLog.id.desc())
            .limit(1)
        )
        lifecycle[-1] = _lifecycle_event(
            "collect",
            collection_job.status,
            {
                "job_id": str(collection_job.id),
                "items_collected": collection_log.items_collected if collection_log else 0,
                "items_inserted": collection_log.items_inserted if collection_log else 0,
                "items_skipped": collection_log.items_skipped if collection_log else 0,
            },
        )
        collection_summary = {
            "job_id": str(collection_job.id),
            "status": collection_job.status,
            "items_collected": collection_log.items_collected if collection_log else 0,
            "items_inserted": collection_log.items_inserted if collection_log else 0,
            "items_skipped": collection_log.items_skipped if collection_log else 0,
        }
        if collection_job.status != "success":
            run.status = "failed"
            run.stage = "collect"
            run.error_summary = collection_job.error_summary or f"Collection finished with status {collection_job.status}."
            run.result_summary = _redact(
                {
                    "lifecycle": lifecycle,
                    "collection": collection_summary,
                }
            )
            run.finished_at = datetime.now(UTC)
            return commit_and_refresh(db, run)

        lifecycle.append(_lifecycle_event("process", "running"))
        run.stage = "process"
        processing_summary = processing_pipeline.process_project(
            db=db,
            project_id=payload.project_id,
            mode=payload.processing_mode,
            reprocess=payload.reprocess,
        )
        lifecycle[-1] = _lifecycle_event("process", "success", processing_summary)
        lifecycle.append(_lifecycle_event("review", "ready"))
        lifecycle.append(
            _lifecycle_event(
                "report",
                "ready",
                {
                    "report_surface": "reports page",
                    "closeout_required": True,
                },
            )
        )
        lifecycle.append(
            _lifecycle_event(
                "closeout",
                "success",
                {
                    "rollback_hint": "Use the stored rollback_hint and local production restore runbook if needed.",
                    "real_provider_status": (
                        "NO_GO_REAL_PROVIDER"
                        if preflight["real_collection_requested"] or preflight["real_processing_requested"]
                        else "NOT_REQUESTED"
                    ),
                },
            )
        )
    except Exception as exc:
        db.rollback()
        run = get_run(db, run.id)
        run.status = "failed"
        run.result_summary = _redact({"lifecycle": lifecycle})
        run.error_summary = _redact(str(exc))
        run.finished_at = datetime.now(UTC)
        return commit_and_refresh(db, run)

    run.status = "success"
    run.stage = "closeout"
    run.result_summary = _redact(
        {
            "lifecycle": lifecycle,
            "collection": {
                **collection_summary,
            },
            "processing": processing_summary,
        }
    )
    run.finished_at = datetime.now(UTC)
    return commit_and_refresh(db, run)


def closeout_run(db: Session, run_id: UUID | str, payload: ProductionRunCloseout) -> ProductionLifecycleRun:
    run = get_run(db, run_id)
    run.status = payload.status
    run.stage = "closeout"
    result_summary = dict(run.result_summary or {})
    lifecycle = result_summary.get("lifecycle")
    if not isinstance(lifecycle, list):
        lifecycle = []
    lifecycle.append(_lifecycle_event("closeout", payload.status))
    result_summary["lifecycle"] = lifecycle
    if payload.result_summary is not None:
        result_summary.update(payload.result_summary)
    run.result_summary = _redact(result_summary)
    flag_modified(run, "result_summary")
    if payload.error_summary is not None:
        run.error_summary = _redact(payload.error_summary)
    if payload.rollback_hint is not None:
        run.rollback_hint = _redact(payload.rollback_hint)
    if payload.redacted_logs is not None:
        run.redacted_logs = _redact(payload.redacted_logs)
    run.finished_at = datetime.now(UTC)
    return commit_and_refresh(db, run)


def _preflight(payload: ProductionRunCreate) -> dict[str, Any]:
    missing: list[str] = []
    blocked: list[str] = []
    real_collection = payload.collection_mode not in SAFE_COLLECTION_MODES
    real_processing = payload.processing_mode not in SAFE_PROCESSING_MODES

    if real_collection:
        if not payload.allow_real_platform_write:
            blocked.append("allow_real_platform_write")
        if not env_flag_enabled(REAL_PLATFORM_SMOKE_ENV):
            missing.append(REAL_PLATFORM_SMOKE_ENV)
        if not env_flag_enabled("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE"):
            missing.append("SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE")
        missing.extend(_missing_collection_env(payload.collection_mode))
    if real_processing:
        if not payload.allow_real_llm:
            blocked.append("allow_real_llm")
        if not payload.allow_real_embedding:
            blocked.append("allow_real_embedding")
        if not env_flag_enabled("SIGNALFORGE_ALLOW_REAL_LLM_SMOKE"):
            missing.append("SIGNALFORGE_ALLOW_REAL_LLM_SMOKE")
        if not env_flag_enabled("SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE"):
            missing.append("SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE")
        missing.extend(name for name in REQUIRED_LLM_ENV if not os.getenv(name, "").strip())

    return {
        "safe_execution": not missing and not blocked,
        "collection_mode": payload.collection_mode,
        "processing_mode": payload.processing_mode,
        "real_collection_requested": real_collection,
        "real_processing_requested": real_processing,
        "missing": missing,
        "blocked": blocked,
        "checked_env": [
            REAL_PLATFORM_SMOKE_ENV,
            "SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE",
            "SIGNALFORGE_ALLOW_REAL_LLM_SMOKE",
            "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE",
        ],
    }


def _missing_collection_env(collection_mode: str) -> list[str]:
    modes = {collection_mode}
    if collection_mode == "p0_real":
        modes = {"reddit", "product_hunt"}

    required: list[str] = []
    if "reddit" in modes:
        required.extend(REDDIT_ENV_VARS)
    if "product_hunt" in modes:
        required.extend(PRODUCT_HUNT_ENV_VARS)

    return [name for name in dict.fromkeys(required) if not os.getenv(name, "").strip()]


def _lifecycle_event(stage: str, status: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    event: dict[str, Any] = {
        "stage": stage,
        "status": status,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    if details:
        event["details"] = _redact(details)
    return event


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if _sensitive_key(str(key)):
                redacted[key] = REDACTED
            else:
                redacted[key] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, tuple):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        redacted_value = value
        for env_name, env_value in os.environ.items():
            if _sensitive_key(env_name) and env_value and len(env_value) >= 4:
                redacted_value = redacted_value.replace(env_value, REDACTED)
        if any(marker in redacted_value.lower() for marker in ("token=", "secret=", "authorization:", "bearer ")):
            return REDACTED
        return redacted_value
    return value


def _sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)
