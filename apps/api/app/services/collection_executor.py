from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector
from app.connectors.mock import MockConnector
from app.connectors.registry import registry
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig
from app.db.models import CollectionJob, Keyword, Project, RawItem
from app.services.collection_jobs import create_collection_job, finish_collection_job, start_collection_job
from app.services.collection_logs import create_collection_log
from app.services.common import get_or_404


ConnectorSpec = str | BaseConnector


def execute_collection(
    db: Session,
    *,
    project_id: UUID,
    execution_mode: str | None = None,
    connectors: Sequence[ConnectorSpec] | None = None,
    job: CollectionJob | None = None,
) -> CollectionJob:
    get_or_404(db, Project, project_id, "Project")
    active_job = job if job is not None else create_collection_job(db, project_id)
    if active_job.project_id != project_id:
        raise ValueError("collection job project_id does not match requested project_id")
    start_collection_job(db, active_job)

    connector_specs = list(connectors) if connectors is not None else _connector_specs_for_mode(execution_mode)
    log_statuses: list[str] = []
    error_messages: list[str] = []

    for connector_spec in connector_specs:
        connector = _resolve_connector(connector_spec)
        platform = connector.platform
        config = _build_project_config(db, project_id, platform)

        try:
            result = connector.collect(config)
        except Exception as exc:  # pragma: no cover - exact connector exceptions are implementation-specific.
            message = str(exc)
            create_collection_log(
                db,
                job_id=active_job.id,
                platform=platform,
                status=ConnectorStatus.FAILED.value,
                error_message=message,
            )
            log_statuses.append(ConnectorStatus.FAILED.value)
            error_messages.append(f"{platform}: {message}")
            continue

        status = _status_value(getattr(result, "status", ConnectorStatus.FAILED))
        items = list(getattr(result, "items", []) or [])
        items_collected = int(getattr(result, "items_collected", 0) or len(items))
        if status == ConnectorStatus.SUCCESS.value:
            inserted, skipped = _insert_raw_items(db, project_id, platform, items)
        else:
            inserted = 0
            skipped = 0
        connector_skipped = int(getattr(result, "items_skipped", 0) or 0)
        skipped += connector_skipped

        error_message = getattr(result, "error_message", None)
        rate_limit_state = getattr(result, "rate_limit_state", None)
        create_collection_log(
            db,
            job_id=active_job.id,
            platform=getattr(result, "platform", platform) or platform,
            status=status,
            items_collected=items_collected,
            items_inserted=inserted,
            items_skipped=skipped,
            error_message=error_message,
            rate_limit_remaining=getattr(rate_limit_state, "remaining", None),
            rate_limit_reset_at=getattr(rate_limit_state, "reset_at", None),
        )
        log_statuses.append(status)
        if error_message and status not in {ConnectorStatus.SUCCESS.value, ConnectorStatus.DISABLED.value}:
            error_messages.append(f"{platform}: {error_message}")

    final_status = _final_job_status(log_statuses)
    finish_collection_job(
        db,
        active_job,
        status=final_status,
        error_summary="; ".join(error_messages) or None,
    )
    db.commit()
    db.refresh(active_job)
    return active_job


def _connector_specs_for_mode(execution_mode: str | None) -> list[ConnectorSpec]:
    if execution_mode is None or execution_mode.strip() == "":
        return ["mock"]
    return [execution_mode.strip()]


def _resolve_connector(connector_spec: ConnectorSpec) -> BaseConnector:
    if isinstance(connector_spec, BaseConnector):
        return connector_spec
    platform = connector_spec.strip()
    if platform == "mock":
        return MockConnector()
    return registry.get(platform)


def _build_project_config(db: Session, project_id: UUID, platform: str) -> ProjectCollectionConfig:
    keywords = list(
        db.scalars(
            select(Keyword)
            .where(Keyword.project_id == project_id)
            .where(Keyword.enabled.is_(True))
            .order_by(Keyword.created_at.asc(), Keyword.id.asc())
        )
    )
    include_keywords = [keyword.keyword for keyword in keywords if keyword.keyword_type != "exclude"]
    exclude_keywords = [keyword.keyword for keyword in keywords if keyword.keyword_type == "exclude"]
    languages = _unique_preserving_order(keyword.language for keyword in keywords if keyword.language != "all")
    return ProjectCollectionConfig(
        project_id=project_id,
        platform=platform,
        keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        languages=languages,
    )


def _unique_preserving_order(values: Sequence[str] | Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _insert_raw_items(
    db: Session,
    project_id: UUID,
    platform: str,
    items: Sequence[Any],
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    for item in items:
        raw_values = _raw_item_values(project_id, platform, item)
        if raw_values is None:
            skipped += 1
            continue

        try:
            with db.begin_nested():
                db.add(RawItem(**raw_values))
                db.flush()
        except IntegrityError:
            skipped += 1
            continue
        inserted += 1

    return inserted, skipped


def _raw_item_values(project_id: UUID, fallback_platform: str, item: Any) -> dict[str, Any] | None:
    data = _item_data(item)
    source_url = _clean_required_text(data.get("source_url"))
    platform = _clean_required_text(data.get("platform")) or fallback_platform
    platform_item_id = _clean_required_text(data.get("platform_item_id"))

    if source_url is None or platform_item_id is None:
        return None

    collected_at = data.get("collected_at") or datetime.now(UTC)
    return {
        "project_id": project_id,
        "platform": platform,
        "platform_item_id": platform_item_id,
        "source_url": source_url,
        "author_hash": data.get("author_hash"),
        "content_text": data.get("content_text"),
        "content_excerpt": data.get("content_excerpt"),
        "normalized_text": data.get("normalized_text"),
        "language": data.get("language"),
        "engagement": data.get("engagement"),
        "keyword_hits": list(data.get("keyword_hits") or []),
        "raw_payload": dict(data.get("raw_payload") or {}),
        "deleted_at_source": bool(data.get("deleted_at_source", False)),
        "created_at_source": data.get("created_at_source"),
        "collected_at": collected_at,
    }


def _item_data(item: Any) -> dict[str, Any]:
    if hasattr(item, "model_dump"):
        return dict(item.model_dump())
    if isinstance(item, Mapping):
        return dict(item)
    fields = (
        "platform",
        "platform_item_id",
        "source_url",
        "author_hash",
        "content_text",
        "content_excerpt",
        "normalized_text",
        "language",
        "engagement",
        "keyword_hits",
        "raw_payload",
        "deleted_at_source",
        "created_at_source",
        "collected_at",
    )
    return {field: getattr(item, field) for field in fields if hasattr(item, field)}


def _clean_required_text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _status_value(status: Any) -> str:
    return getattr(status, "value", str(status))


def _final_job_status(log_statuses: Sequence[str]) -> str:
    if not log_statuses:
        return ConnectorStatus.FAILED.value

    disabled = ConnectorStatus.DISABLED.value
    success = ConnectorStatus.SUCCESS.value
    rate_limited = ConnectorStatus.RATE_LIMITED.value
    failed_statuses = {ConnectorStatus.FAILED.value, ConnectorStatus.PERMISSION_LIMITED.value}

    effective_statuses = [status for status in log_statuses if status != disabled]
    if not effective_statuses:
        return success
    if all(status == rate_limited for status in effective_statuses):
        return rate_limited
    if all(status in failed_statuses for status in effective_statuses):
        return ConnectorStatus.FAILED.value
    if any(status in failed_statuses or status == rate_limited for status in effective_statuses):
        if any(status == success for status in effective_statuses):
            return "partial_failed"
        return ConnectorStatus.FAILED.value
    return success
