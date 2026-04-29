from __future__ import annotations

from app.processing.redactor import (
    EMAIL_REDACTION,
    PHONE_REDACTION,
    SEED_PHRASE_REDACTION,
    WALLET_REDACTION,
    redact_sensitive_text,
)


def test_redactor_removes_sensitive_values_before_classification() -> None:
    text = (
        "Need alerts for wallet 0x0123456789abcdef0123456789abcdef01234567. "
        "Contact alpha@example.com or +1 415-555-1212. "
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
    assert "abandon ability able" not in result.redacted_text
