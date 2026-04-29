from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_SIGNAL_TYPES: tuple[str, ...] = (
    "complaint",
    "feature_request",
    "alternative_search",
    "pricing_issue",
    "security_concern",
    "workflow_pain",
    "integration_need",
    "learning_barrier",
    "positive_feedback",
    "noise",
)

SCORE_FIELDS: tuple[str, ...] = (
    "pain_level",
    "clarity_score",
    "urgency_score",
    "business_relevance",
    "model_confidence",
    "signal_confidence",
)


def clamp_score(value: Any, *, default: int = 0) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = default
    return max(0, min(100, score))


def normalize_signal_type(value: Any) -> str:
    signal_type = str(value or "").strip()
    return signal_type if signal_type in ALLOWED_SIGNAL_TYPES else "noise"


@dataclass(frozen=True)
class ProcessingCounters:
    llm_json_failure_count: int = 0
    fallback_classification_count: int = 0

    def model_dump(self) -> dict[str, int]:
        return {
            "llm_json_failure_count": self.llm_json_failure_count,
            "fallback_classification_count": self.fallback_classification_count,
        }


@dataclass(frozen=True)
class ClassificationResult:
    is_need_signal: bool
    signal_type: str
    pain_level: int
    clarity_score: int
    urgency_score: int
    business_relevance: int
    model_confidence: int
    signal_confidence: int
    summary_zh: str
    recommended_action: str
    counters: ProcessingCounters = field(default_factory=ProcessingCounters)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "signal_type", normalize_signal_type(self.signal_type))
        for field_name in SCORE_FIELDS:
            object.__setattr__(self, field_name, clamp_score(getattr(self, field_name)))
        object.__setattr__(self, "summary_zh", str(self.summary_zh or "").strip())
        object.__setattr__(self, "recommended_action", str(self.recommended_action or "").strip())

    def model_dump(self) -> dict[str, Any]:
        return {
            "is_need_signal": self.is_need_signal,
            "signal_type": self.signal_type,
            "pain_level": self.pain_level,
            "clarity_score": self.clarity_score,
            "urgency_score": self.urgency_score,
            "business_relevance": self.business_relevance,
            "model_confidence": self.model_confidence,
            "signal_confidence": self.signal_confidence,
            "summary_zh": self.summary_zh,
            "recommended_action": self.recommended_action,
            "counters": self.counters.model_dump(),
            "metadata": dict(self.metadata),
        }

    def signal_values(self) -> dict[str, Any]:
        return {
            "is_need_signal": self.is_need_signal,
            "signal_type": self.signal_type,
            "pain_level": self.pain_level,
            "clarity_score": self.clarity_score,
            "urgency_score": self.urgency_score,
            "business_relevance": self.business_relevance,
            "model_confidence": self.model_confidence,
            "signal_confidence": self.signal_confidence,
            "summary_zh": self.summary_zh,
            "recommended_action": self.recommended_action,
        }
