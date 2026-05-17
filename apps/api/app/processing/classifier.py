from __future__ import annotations

import json
import os
import re
from dataclasses import replace
from typing import Any, Mapping

from app.processing.llm_client import (
    LLMProviderError,
    OpenAICompatibleLLMClient,
    missing_llm_env,
    real_llm_processing_enabled,
)
from app.processing.types import (
    ALLOWED_SIGNAL_TYPES,
    SCORE_FIELDS,
    ClassificationResult,
    ProcessingCounters,
    clamp_score,
    normalize_signal_type,
)


class ClassificationValidationError(ValueError):
    pass


FALLBACK_RULES: tuple[tuple[str, str, int, str], ...] = (
    ("is there any tool", "alternative_search", 84, "Evaluate tool gap and compare existing alternatives."),
    ("looking for", "alternative_search", 80, "Review alternative-search demand and competing workflows."),
    ("alternative", "alternative_search", 78, "Map alternative demand to existing product gaps."),
    ("expensive", "pricing_issue", 76, "Validate pricing pain and willingness to switch."),
    ("unsafe", "security_concern", 82, "Investigate trust, permission, and safety concerns."),
    ("need a less confusing", "workflow_pain", 78, "Inspect the workflow friction and missing automation."),
    ("confusing", "learning_barrier", 74, "Simplify onboarding or clarify the workflow."),
    ("too noisy", "workflow_pain", 79, "Assess summarization or filtering opportunity."),
    ("hard to", "workflow_pain", 75, "Inspect the workflow friction and missing automation."),
    ("missing", "feature_request", 73, "Validate requested capability and frequency."),
    ("wish", "feature_request", 72, "Validate requested capability with more evidence."),
    ("need", "workflow_pain", 71, "Validate urgency and target workflow."),
)

NOISE_TERMS = ("giveaway", "airdrop", "referral", "hiring")


def classify_text(text: str, *, mode: str = "mock", llm_payload: Any | None = None) -> ClassificationResult:
    safe_text = _safe_text(text)
    if mode == "fallback_only":
        return fallback_classify(safe_text, reason="fallback_only")
    if mode == "real_llm_classification":
        return real_llm_classify(safe_text, llm_payload=llm_payload)
    if mode != "mock":
        raise ValueError("Processing classifier only supports mock, fallback_only, and real_llm_classification modes.")
    if llm_payload is not None:
        return classify_llm_payload_or_fallback(llm_payload, safe_text)
    return mock_llm_classify(safe_text)


def mock_llm_classify(text: str) -> ClassificationResult:
    safe_text = _safe_text(text)
    fallback = fallback_classify(safe_text, reason="mock_seed")
    payload = fallback.signal_values()
    payload["model_confidence"] = min(78, max(55, fallback.model_confidence + 18))
    payload["signal_confidence"] = min(90, max(fallback.signal_confidence, fallback.signal_confidence + 10))
    return validate_classification_payload(
        payload,
        metadata={
            "classification_source": "mock_llm",
            "matched_rule": fallback.metadata.get("matched_rule"),
        },
    )


def real_llm_classify(
    text: str,
    *,
    llm_payload: Any | None = None,
    env: Mapping[str, str] | None = None,
    client: OpenAICompatibleLLMClient | None = None,
) -> ClassificationResult:
    safe_text = _safe_text(text)
    if llm_payload is not None:
        return classify_llm_payload_or_fallback(llm_payload, safe_text, source="real_llm_payload")
    if not real_llm_processing_enabled(env):
        return fallback_classify(
            safe_text,
            reason="real_llm_disabled",
            counters=ProcessingCounters(llm_json_failure_count=1, fallback_classification_count=1),
            metadata={"classification_source": "real_llm_fallback"},
        )
    missing = missing_llm_env(env)
    if missing:
        return fallback_classify(
            safe_text,
            reason="real_llm_missing_env",
            counters=ProcessingCounters(llm_json_failure_count=1, fallback_classification_count=1),
            metadata={"classification_source": "real_llm_fallback", "missing_required_env_count": len(missing)},
        )
    try:
        active_client = client or _real_llm_client(env)
        return classify_llm_payload_or_fallback(
            active_client.classify_signal(safe_text),
            safe_text,
            source="real_llm",
        )
    except LLMProviderError as exc:
        return fallback_classify(
            safe_text,
            reason="real_llm_provider_error",
            counters=ProcessingCounters(llm_json_failure_count=1, fallback_classification_count=1),
            metadata={"classification_source": "real_llm_fallback", "provider_error": _redact_provider_error(str(exc))},
        )


def classify_llm_payload_or_fallback(payload: Any, fallback_text: str, *, source: str = "llm_payload") -> ClassificationResult:
    try:
        return validate_classification_payload(payload, metadata={"classification_source": source})
    except ClassificationValidationError as exc:
        return fallback_classify(
            fallback_text,
            reason="llm_json_invalid",
            counters=ProcessingCounters(llm_json_failure_count=1, fallback_classification_count=1),
            metadata={"validation_error": str(exc), "classification_source": f"{source}_fallback"},
        )


def _real_llm_client(env: Mapping[str, str] | None) -> OpenAICompatibleLLMClient:
    source = env or os.environ
    return OpenAICompatibleLLMClient(
        base_url=source["LLM_BASE_URL"],
        api_key=source["LLM_API_KEY"],
        model=source["LLM_MODEL"],
    )


def validate_classification_payload(
    payload: Any,
    *,
    metadata: dict[str, Any] | None = None,
) -> ClassificationResult:
    data = _coerce_payload(payload)
    missing = [field for field in _required_fields() if field not in data]
    if missing:
        raise ClassificationValidationError(f"missing required fields: {', '.join(sorted(missing))}")

    signal_type = str(data["signal_type"]).strip()
    if signal_type not in ALLOWED_SIGNAL_TYPES:
        raise ClassificationValidationError(f"invalid signal_type: {signal_type}")

    for field_name in SCORE_FIELDS:
        if not _is_number(data[field_name]):
            raise ClassificationValidationError(f"{field_name} must be numeric")
        numeric = float(data[field_name])
        if numeric < 0 or numeric > 100:
            raise ClassificationValidationError(f"{field_name} must be between 0 and 100")

    return ClassificationResult(
        is_need_signal=bool(data["is_need_signal"]),
        signal_type=signal_type,
        pain_level=clamp_score(data["pain_level"]),
        clarity_score=clamp_score(data["clarity_score"]),
        urgency_score=clamp_score(data["urgency_score"]),
        business_relevance=clamp_score(data["business_relevance"]),
        model_confidence=clamp_score(data["model_confidence"]),
        signal_confidence=clamp_score(data["signal_confidence"]),
        summary_zh=str(data["summary_zh"]).strip(),
        recommended_action=str(data["recommended_action"]).strip(),
        counters=ProcessingCounters(),
        metadata=metadata or {},
    )


def fallback_classify(
    text: str,
    *,
    reason: str = "keyword_fallback",
    counters: ProcessingCounters | None = None,
    metadata: dict[str, Any] | None = None,
) -> ClassificationResult:
    safe_text = _safe_text(text)
    lowered = safe_text.lower()
    matched_rule: tuple[str, str, int, str] | None = None
    for rule in FALLBACK_RULES:
        if rule[0] in lowered:
            matched_rule = rule
            break

    if any(term in lowered for term in NOISE_TERMS):
        result = ClassificationResult(
            is_need_signal=False,
            signal_type="noise",
            pain_level=20,
            clarity_score=35,
            urgency_score=20,
            business_relevance=20,
            model_confidence=28,
            signal_confidence=25,
            summary_zh="疑似噪音内容，暂不作为高价值需求信号。",
            recommended_action="Ignore for opportunity scoring unless repeated by credible sources.",
            counters=counters or ProcessingCounters(fallback_classification_count=1),
            metadata={"classification_source": "fallback", "fallback_reason": reason, "matched_rule": "noise"},
        )
        return _merge_metadata(result, metadata)

    if matched_rule is None:
        result = ClassificationResult(
            is_need_signal=False,
            signal_type="noise",
            pain_level=30,
            clarity_score=35,
            urgency_score=25,
            business_relevance=30,
            model_confidence=32,
            signal_confidence=30,
            summary_zh="未检测到明确需求或痛点。",
            recommended_action="Keep as low-priority evidence unless more similar items appear.",
            counters=counters or ProcessingCounters(fallback_classification_count=1),
            metadata={"classification_source": "fallback", "fallback_reason": reason, "matched_rule": None},
        )
        return _merge_metadata(result, metadata)

    keyword, signal_type, pain_level, action = matched_rule
    clarity = 72 if len(safe_text) >= 40 else 58
    urgency = 76 if keyword in {"need", "unsafe", "too noisy", "is there any tool"} else 66
    relevance = 78 if signal_type != "noise" else 30
    model_confidence = 42
    signal_confidence = clamp_score((pain_level * 0.45) + (clarity * 0.20) + (urgency * 0.20) + (relevance * 0.15))

    result = ClassificationResult(
        is_need_signal=True,
        signal_type=signal_type,
        pain_level=pain_level,
        clarity_score=clarity,
        urgency_score=urgency,
        business_relevance=relevance,
        model_confidence=model_confidence,
        signal_confidence=signal_confidence,
        summary_zh=_summary_for(signal_type, safe_text),
        recommended_action=action,
        counters=counters or ProcessingCounters(fallback_classification_count=1),
        metadata={"classification_source": "fallback", "fallback_reason": reason, "matched_rule": keyword},
    )
    return _merge_metadata(result, metadata)


def _coerce_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, str):
        try:
            loaded = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ClassificationValidationError("invalid JSON") from exc
        if not isinstance(loaded, dict):
            raise ClassificationValidationError("classification JSON must be an object")
        return loaded
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        dumped = payload.model_dump()
        if isinstance(dumped, dict):
            return dumped
    raise ClassificationValidationError("classification payload must be a dict or JSON object")


def _required_fields() -> tuple[str, ...]:
    return (
        "is_need_signal",
        "signal_type",
        "pain_level",
        "clarity_score",
        "urgency_score",
        "business_relevance",
        "model_confidence",
        "signal_confidence",
        "summary_zh",
        "recommended_action",
    )


def _is_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _safe_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _redact_provider_error(message: str) -> str:
    redacted = str(message or "")
    redacted = re.sub(r"(?i)bearer\\s+\\S+", "[REDACTED]", redacted)
    redacted = re.sub(r"(?i)(token|secret|api_key|authorization)", "[REDACTED]", redacted)
    return redacted


def _summary_for(signal_type: str, text: str) -> str:
    excerpt = text[:120].strip()
    if signal_type == "pricing_issue":
        return f"用户表达了价格或成本痛点：{excerpt}"
    if signal_type == "alternative_search":
        return f"用户正在寻找替代方案或工具空白：{excerpt}"
    if signal_type == "security_concern":
        return f"用户表达了安全或信任顾虑：{excerpt}"
    if signal_type == "feature_request":
        return f"用户提出了明确功能诉求：{excerpt}"
    if signal_type == "learning_barrier":
        return f"用户遇到理解或上手障碍：{excerpt}"
    return f"用户表达了工作流痛点或需求：{excerpt}"


def _merge_metadata(result: ClassificationResult, extra: dict[str, Any] | None) -> ClassificationResult:
    if not extra:
        return result
    merged = dict(result.metadata)
    merged.update(extra)
    return replace(result, metadata=merged)
