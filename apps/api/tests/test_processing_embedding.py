from __future__ import annotations

import math

from app.processing.embedding_client import (
    EMBEDDING_DIMENSION,
    MockEmbeddingClient,
    deterministic_mock_embedding,
    validate_embedding,
)


def test_mock_embedding_is_deterministic_and_1536_dimensional() -> None:
    text = "I need better alerts when prediction market odds move."

    first = deterministic_mock_embedding(text)
    second = deterministic_mock_embedding(text)

    assert len(first) == EMBEDDING_DIMENSION
    assert first == second
    assert math.isclose(math.sqrt(sum(value * value for value in first)), 1.0, rel_tol=1e-9)


def test_mock_embedding_changes_for_different_text() -> None:
    first = deterministic_mock_embedding("wallet integration feels unsafe")
    second = deterministic_mock_embedding("looking for cheaper analytics tools")

    assert first != second


def test_mock_embedding_client_returns_model_name_and_valid_vector() -> None:
    result = MockEmbeddingClient().embed_text("Discord alpha groups are too noisy.")

    assert result.model_name == "signalforge-mock-embedding-v1"
    assert result.text == "Discord alpha groups are too noisy."
    validate_embedding(result.embedding)
