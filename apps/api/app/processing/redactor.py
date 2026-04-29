from __future__ import annotations

import re
from dataclasses import dataclass


EMAIL_REDACTION = "[REDACTED_EMAIL]"
PHONE_REDACTION = "[REDACTED_PHONE]"
WALLET_REDACTION = "[REDACTED_WALLET]"
SEED_PHRASE_REDACTION = "[REDACTED_SEED_PHRASE]"

_EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\w)"
)
_ETHEREUM_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
_BITCOIN_PATTERN = re.compile(r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}\b")
_SOLANA_PATTERN = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
_SEED_LABEL_PATTERN = re.compile(
    r"(?i)\b(?:seed phrase|recovery phrase|mnemonic|private seed)\b\s*[:=-]?\s*"
    r"((?:[a-z]{3,12}\s+){11,23}[a-z]{3,12})"
)


@dataclass(frozen=True)
class RedactionResult:
    redacted_text: str
    redaction_applied: bool
    redaction_types: tuple[str, ...]


def redact_sensitive_text(text: str | None) -> RedactionResult:
    value = "" if text is None else str(text)
    redaction_types: list[str] = []

    value, count = _SEED_LABEL_PATTERN.subn(SEED_PHRASE_REDACTION, value)
    if count:
        redaction_types.append("seed_phrase")

    value, count = _EMAIL_PATTERN.subn(EMAIL_REDACTION, value)
    if count:
        redaction_types.append("email")

    value, count = _PHONE_PATTERN.subn(PHONE_REDACTION, value)
    if count:
        redaction_types.append("phone")

    value, wallet_count = _ETHEREUM_PATTERN.subn(WALLET_REDACTION, value)
    value, count = _BITCOIN_PATTERN.subn(WALLET_REDACTION, value)
    wallet_count += count
    value, count = _SOLANA_PATTERN.subn(_redact_probable_solana_wallet, value)
    wallet_count += count
    if wallet_count:
        redaction_types.append("wallet")

    return RedactionResult(
        redacted_text=value,
        redaction_applied=bool(redaction_types),
        redaction_types=tuple(dict.fromkeys(redaction_types)),
    )


def _redact_probable_solana_wallet(match: re.Match[str]) -> str:
    value = match.group(0)
    has_digit = any(char.isdigit() for char in value)
    has_lower = any(char.islower() for char in value)
    has_upper = any(char.isupper() for char in value)
    if has_digit and (has_lower or has_upper):
        return WALLET_REDACTION
    return value
