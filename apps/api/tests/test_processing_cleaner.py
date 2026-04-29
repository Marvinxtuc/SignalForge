from __future__ import annotations

from app.processing import prepare_text_for_processing
from app.processing.cleaner import build_excerpt, clean_text, normalize_for_matching
from app.processing.duplicate import collapse_duplicate_texts, duplicate_key
from app.processing.language import detect_language
from app.processing.noise_filter import assess_noise
from app.processing.redactor import (
    EMAIL_REDACTION,
    PHONE_REDACTION,
    SEED_PHRASE_REDACTION,
    WALLET_REDACTION,
    redact_sensitive_text,
)


def test_clean_text_normalizes_whitespace_html_and_tracking_params() -> None:
    cleaned = clean_text("  Polymarket&nbsp; alerts\n\nare useful   https://x.test?a=1&utm_source=spam ")

    assert cleaned == "Polymarket alerts are useful https://x.test?a=1"


def test_build_excerpt_is_deterministic() -> None:
    assert build_excerpt("a" * 20, max_length=10) == "aaaaaaaaa..."


def test_normalize_for_matching_removes_punctuation_and_case() -> None:
    assert normalize_for_matching("Better ALERTS, please!") == "better alerts please"


def test_redacts_email_phone_wallet_and_seed_phrase() -> None:
    text = (
        "Email me at alpha@example.com or +1 (415) 555-1212. "
        "Wallet 0x0123456789abcdef0123456789abcdef01234567. "
        "seed phrase: abandon ability able about above absent absorb abstract absurd abuse access accident"
    )

    result = redact_sensitive_text(text)

    assert result.redaction_applied is True
    assert EMAIL_REDACTION in result.redacted_text
    assert PHONE_REDACTION in result.redacted_text
    assert WALLET_REDACTION in result.redacted_text
    assert SEED_PHRASE_REDACTION in result.redacted_text
    assert "alpha@example.com" not in result.redacted_text
    assert "0123456789abcdef" not in result.redacted_text
    assert set(result.redaction_types) == {"email", "phone", "wallet", "seed_phrase"}


def test_detect_language_uses_local_heuristics() -> None:
    assert detect_language("I need better prediction market alerts") == "en"
    assert detect_language("我需要更好的预测市场提醒") == "zh"
    assert detect_language("12345") == "unknown"


def test_noise_filter_downgrades_short_and_promotional_content() -> None:
    assert assess_noise("gm").is_noise is False

    promotional = assess_noise("Free giveaway airdrop referral code apply now")

    assert promotional.is_noise is True
    assert promotional.noise_score >= 70
    assert "giveaway" in promotional.reasons
    assert "airdrop" in promotional.reasons
    assert "referral" in promotional.reasons


def test_duplicate_key_is_stable_and_collapse_preserves_first_item() -> None:
    assert duplicate_key("Better alerts!") == duplicate_key("better alerts")

    items = [
        {"id": 1, "text": "Better alerts!"},
        {"id": 2, "text": "better alerts"},
        {"id": 3, "text": "Need portfolio tracking"},
    ]
    unique = collapse_duplicate_texts(items, text_getter=lambda item: item["text"])

    assert [item["id"] for item in unique] == [1, 3]


def test_prepare_text_for_processing_returns_pipeline_ready_fields() -> None:
    prepared = prepare_text_for_processing("Need alerts for 0x0123456789abcdef0123456789abcdef01234567")

    assert prepared.cleaned_text.startswith("Need alerts")
    assert prepared.redaction_applied is True
    assert prepared.language == "en"
    assert prepared.noise_score < 70
    assert WALLET_REDACTION in prepared.redacted_text
