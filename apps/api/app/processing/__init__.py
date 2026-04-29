from __future__ import annotations

from dataclasses import dataclass

from app.processing.cleaner import clean_text
from app.processing.duplicate import collapse_duplicate_texts, duplicate_key
from app.processing.language import detect_language
from app.processing.noise_filter import NoiseAssessment, assess_noise
from app.processing.redactor import RedactionResult, redact_sensitive_text


@dataclass(frozen=True)
class PreparedText:
    cleaned_text: str
    redacted_text: str
    language: str
    noise_score: int
    redaction_applied: bool
    redaction_types: tuple[str, ...]
    noise_reasons: tuple[str, ...]


def prepare_text_for_processing(text: str | None) -> PreparedText:
    cleaned_text = clean_text(text)
    redaction = redact_sensitive_text(cleaned_text)
    language = detect_language(redaction.redacted_text)
    noise = assess_noise(redaction.redacted_text)

    return PreparedText(
        cleaned_text=cleaned_text,
        redacted_text=redaction.redacted_text,
        language=language,
        noise_score=noise.noise_score,
        redaction_applied=redaction.redaction_applied,
        redaction_types=redaction.redaction_types,
        noise_reasons=noise.reasons,
    )


__all__ = [
    "NoiseAssessment",
    "PreparedText",
    "RedactionResult",
    "assess_noise",
    "clean_text",
    "collapse_duplicate_texts",
    "detect_language",
    "duplicate_key",
    "prepare_text_for_processing",
    "redact_sensitive_text",
]
