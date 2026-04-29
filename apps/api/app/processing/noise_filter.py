from __future__ import annotations

import re
from dataclasses import dataclass

from app.processing.cleaner import normalize_for_matching


_NOISE_TERMS = {
    "airdrop": 35,
    "giveaway": 35,
    "referral": 35,
    "referral code": 45,
    "use my code": 45,
    "hiring": 35,
    "we are hiring": 45,
    "apply now": 35,
    "free money": 35,
    "follow and retweet": 45,
    "limited time offer": 30,
}
_URL_ONLY_PATTERN = re.compile(r"^(?:https?://\S+\s*)+$", re.IGNORECASE)


@dataclass(frozen=True)
class NoiseAssessment:
    noise_score: int
    reasons: tuple[str, ...]
    is_noise: bool


def assess_noise(text: str | None) -> NoiseAssessment:
    raw = "" if text is None else str(text)
    normalized = normalize_for_matching(raw)
    reasons: list[str] = []
    score = 0

    if not normalized:
        score += 100
        reasons.append("empty")
    elif len(normalized) < 12:
        score += 50
        reasons.append("too_short")
    elif len(normalized.split()) < 4:
        score += 30
        reasons.append("low_context")

    if _URL_ONLY_PATTERN.match(raw.strip()):
        score += 60
        reasons.append("url_only")

    for term, weight in _NOISE_TERMS.items():
        if term in normalized:
            score += weight
            reasons.append(term.replace(" ", "_"))

    score = max(0, min(100, score))
    return NoiseAssessment(
        noise_score=score,
        reasons=tuple(dict.fromkeys(reasons)),
        is_noise=score >= 70,
    )
