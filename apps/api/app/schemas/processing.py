from __future__ import annotations

from typing import Any
from uuid import UUID

from app.schemas.common import ApiSchema


class ProcessingRequest(ApiSchema):
    mode: str = "mock"
    reprocess: bool = False


class ProcessingTopSignal(ApiSchema):
    signal_id: str
    raw_item_id: str
    platform: str
    source_url: str
    signal_type: str | None = None
    pain_level: int | None = None
    signal_confidence: int | None = None
    summary_zh: str | None = None


class ProcessingSummary(ApiSchema):
    total_raw_items: int
    processed_raw_items: int
    total_signals: int
    high_value_signals: int
    high_value_ratio: float
    noise_ratio: float
    llm_json_failure_count: int
    fallback_classification_count: int
    cluster_coverage_rate: float
    opportunity_count: int
    embedding_count: int = 0
    cluster_count: int = 0
    top_5_high_value_signals: list[ProcessingTopSignal]


class ProcessingResponse(ProcessingSummary):
    project_id: UUID
    mode: str
    reprocess: bool
    processed_in_run: int
    skipped_existing: int
    skipped_deleted: int
    status: str = "success"
    details: dict[str, Any] = {}
