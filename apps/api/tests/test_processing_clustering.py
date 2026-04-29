from __future__ import annotations

import math

from app.processing.clustering import DEFAULT_SIMILARITY_THRESHOLD, cosine_similarity
from app.processing.embedding_client import deterministic_mock_embedding
from app.processing.opportunity_scoring import calculate_opportunity_score, clamp_score


def test_cosine_similarity_detects_identical_and_different_vectors() -> None:
    first = deterministic_mock_embedding("better prediction market odds alerts")
    same = deterministic_mock_embedding("better prediction market odds alerts")
    different = deterministic_mock_embedding("wallet integration feels unsafe and confusing")

    assert math.isclose(cosine_similarity(first, same), 1.0, rel_tol=1e-9)
    assert cosine_similarity(first, different) < DEFAULT_SIMILARITY_THRESHOLD


def test_opportunity_score_formula_is_clamped_to_0_100() -> None:
    score = calculate_opportunity_score(
        pain_level_avg=80,
        frequency_score=60,
        source_diversity_score=50,
        clarity_score_avg=70,
        freshness_score=90,
        engagement_score=40,
    )

    assert score == 68
    assert clamp_score(-10) == 0
    assert clamp_score(120) == 100
