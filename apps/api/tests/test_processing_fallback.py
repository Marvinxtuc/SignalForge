from __future__ import annotations

from app.processing.classifier import classify_llm_payload_or_fallback, classify_text
from app.processing.llm_client import run_manual_llm_smoke


def test_invalid_json_uses_fallback_without_crashing() -> None:
    result = classify_llm_payload_or_fallback("{not-json", "Is there any tool to track odds changes?")

    assert result.is_need_signal is True
    assert result.signal_type == "alternative_search"
    assert result.counters.llm_json_failure_count == 1
    assert result.counters.fallback_classification_count == 1
    assert result.metadata["fallback_reason"] == "llm_json_invalid"


def test_missing_fields_use_fallback_without_crashing() -> None:
    result = classify_llm_payload_or_fallback({"signal_type": "workflow_pain"}, "This product is confusing")

    assert result.signal_type == "learning_barrier"
    assert result.counters.llm_json_failure_count == 1
    assert result.counters.fallback_classification_count == 1


def test_fallback_only_mode_never_calls_provider() -> None:
    result = classify_text("Looking for an alternative to expensive analytics", mode="fallback_only")

    assert result.signal_type == "alternative_search"
    assert result.counters.fallback_classification_count == 1


def test_manual_llm_smoke_defaults_to_disabled_without_token() -> None:
    result = run_manual_llm_smoke(env={})

    assert result.status == "DISABLED_MISSING_TOKEN"
    assert result.details["real_provider_called"] is False
