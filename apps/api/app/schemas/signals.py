from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.schemas.common import ApiSchema


SignalStatus = Literal["new", "saved", "ignored", "reviewed"]
SignalFeedback = Literal["valuable", "not_valuable", "wrong_type", "ignored"]


class SignalRead(ApiSchema):
    id: UUID
    raw_item_id: UUID
    project_id: UUID
    is_need_signal: bool
    signal_type: str | None = None
    pain_level: int | None = None
    clarity_score: int | None = None
    urgency_score: int | None = None
    business_relevance: int | None = None
    model_confidence: int | None = None
    signal_confidence: int | None = None
    summary_zh: str | None = None
    recommended_action: str | None = None
    user_feedback: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    platform: str
    source_url: str
    content_excerpt: str | None = None
    keyword_hits: list[str] | None = None
    engagement: dict[str, Any] | None = None
    created_at_source: datetime | None = None


class SignalFeedbackUpdate(ApiSchema):
    user_feedback: SignalFeedback


class SignalStatusUpdate(ApiSchema):
    status: SignalStatus
