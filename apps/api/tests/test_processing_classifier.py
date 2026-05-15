from __future__ import annotations

import pytest

from app.processing.classifier import (
    classify_llm_payload_or_fallback,
    classify_text,
    fallback_classify,
    real_llm_classify,
    validate_classification_payload,
)
from app.processing.llm_client import LLMProviderError
from app.processing.types import ALLOWED_SIGNAL_TYPES, clamp_score


@pytest.mark.parametrize(
    ("text", "expected_type"),
    [
        ("I wish this product had better alerts", "feature_request"),
        ("We need summaries for noisy alpha groups", "workflow_pain"),
        ("The export feature is missing", "feature_request"),
        ("This analytics tool is too expensive", "pricing_issue"),
        ("Looking for a better workflow tracker", "alternative_search"),
        ("Need an alternative to complex crypto analytics", "alternative_search"),
        ("This wallet flow feels unsafe", "security_concern"),
        ("The setup is confusing", "learning_barrier"),
        ("The Discord group is too noisy", "workflow_pain"),
        ("It is hard to track positions", "workflow_pain"),
        ("Is there any tool for odds alerts?", "alternative_search"),
    ],
)
def test_fallback_classifier_detects_required_keywords(text: str, expected_type: str) -> None:
    result = fallback_classify(text)

    assert result.is_need_signal is True
    assert result.signal_type == expected_type
    assert result.pain_level >= 70
    assert result.signal_confidence >= 60
    assert result.counters.fallback_classification_count == 1
    assert result.summary_zh
    assert result.recommended_action


def test_noise_terms_are_downgraded() -> None:
    result = fallback_classify("Hiring referral giveaway airdrop thread")

    assert result.is_need_signal is False
    assert result.signal_type == "noise"
    assert result.pain_level < 70


def test_mock_llm_classifier_returns_phase_1_signal_fields() -> None:
    result = classify_text("I need a safer wallet analytics workflow", mode="mock")
    payload = result.model_dump()

    for key in {
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
    }:
        assert key in payload
    assert result.signal_type in ALLOWED_SIGNAL_TYPES
    assert result.counters.llm_json_failure_count == 0
    assert result.counters.fallback_classification_count == 0


def test_valid_payload_is_accepted_and_scores_are_clamped_helpers_exist() -> None:
    result = validate_classification_payload(
        {
            "is_need_signal": True,
            "signal_type": "workflow_pain",
            "pain_level": 88,
            "clarity_score": 77,
            "urgency_score": 66,
            "business_relevance": 55,
            "model_confidence": 44,
            "signal_confidence": 73,
            "summary_zh": "用户有明确工作流痛点。",
            "recommended_action": "Validate with more examples.",
        }
    )

    assert result.pain_level == 88
    assert clamp_score(101) == 100
    assert clamp_score(-1) == 0


def test_out_of_range_llm_json_falls_back_and_counts_failure() -> None:
    result = classify_llm_payload_or_fallback(
        {
            "is_need_signal": True,
            "signal_type": "workflow_pain",
            "pain_level": 999,
            "clarity_score": 77,
            "urgency_score": 66,
            "business_relevance": 55,
            "model_confidence": 44,
            "signal_confidence": 73,
            "summary_zh": "bad",
            "recommended_action": "bad",
        },
        "I need a less confusing alert workflow",
    )

    assert result.counters.llm_json_failure_count == 1
    assert result.counters.fallback_classification_count == 1
    assert result.signal_type == "workflow_pain"
    assert 0 <= result.pain_level <= 100


def test_real_llm_classifier_accepts_provider_json_from_fake_client() -> None:
    class FakeLLMClient:
        def classify_signal(self, text: str) -> str:
            assert "wallet" in text
            return """{
                "is_need_signal": true,
                "signal_type": "security_concern",
                "pain_level": 86,
                "clarity_score": 80,
                "urgency_score": 78,
                "business_relevance": 82,
                "model_confidence": 76,
                "signal_confidence": 84,
                "summary_zh": "用户担心钱包连接安全。",
                "recommended_action": "Review wallet permissions and trust copy."
            }"""

    result = real_llm_classify(
        "wallet connection feels unsafe",
        env={
            "SIGNALFORGE_ALLOW_REAL_LLM_PROCESSING": "true",
            "LLM_BASE_URL": "https://llm.example.test/v1",
            "LLM_API_KEY": "secret",
            "LLM_MODEL": "test-model",
        },
        client=FakeLLMClient(),
    )

    assert result.signal_type == "security_concern"
    assert result.metadata["classification_source"] == "real_llm"
    assert result.counters.llm_json_failure_count == 0
    assert result.counters.fallback_classification_count == 0


def test_real_llm_classifier_falls_back_on_provider_error_without_leaking_secret() -> None:
    class FailingLLMClient:
        def classify_signal(self, text: str) -> str:
            raise LLMProviderError("Authorization Bearer secret-token failed")

    result = real_llm_classify(
        "Looking for an alternative to expensive analytics",
        env={
            "SIGNALFORGE_ALLOW_REAL_LLM_PROCESSING": "true",
            "LLM_BASE_URL": "https://llm.example.test/v1",
            "LLM_API_KEY": "secret-token",
            "LLM_MODEL": "test-model",
        },
        client=FailingLLMClient(),
    )

    assert result.signal_type == "alternative_search"
    assert result.counters.llm_json_failure_count == 1
    assert result.counters.fallback_classification_count == 1
    assert "secret-token" not in str(result.model_dump())
