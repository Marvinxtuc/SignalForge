from __future__ import annotations

import math

import pytest

from app.processing.embedding_client import (
    EMBEDDING_DIMENSION,
    EmbeddingProviderError,
    MockEmbeddingClient,
    OpenAICompatibleEmbeddingClient,
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


def test_openai_compatible_embedding_client_posts_to_embeddings_endpoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b'{"data":[{"embedding":[' + b",".join([b"0.0"] * EMBEDDING_DIMENSION) + b"]}]}"

    def fake_urlopen(request, *, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["authorization"] = request.headers["Authorization"]
        captured["body"] = request.data.decode("utf-8")
        return FakeResponse()

    monkeypatch.setattr("app.processing.embedding_client.urllib.request.urlopen", fake_urlopen)

    result = OpenAICompatibleEmbeddingClient(
        base_url="https://llm.example.test/v1",
        api_key="secret-value",
        model="text-embedding-3-small",
        timeout_seconds=3.0,
    ).embed_text("Need better alerts")

    assert captured["url"] == "https://llm.example.test/v1/embeddings"
    assert captured["authorization"] == "Bearer secret-value"
    assert '"model": "text-embedding-3-small"' in captured["body"]
    assert result.model_name == "text-embedding-3-small"
    assert len(result.embedding) == EMBEDDING_DIMENSION


def test_openai_compatible_embedding_client_rejects_invalid_dimensions(monkeypatch) -> None:
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def read(self, _limit: int) -> bytes:
            return b'{"data":[{"embedding":[0.1,0.2]}]}'

    monkeypatch.setattr(
        "app.processing.embedding_client.urllib.request.urlopen",
        lambda request, *, timeout: FakeResponse(),
    )

    client = OpenAICompatibleEmbeddingClient(
        base_url="https://llm.example.test",
        api_key="secret-value",
        model="text-embedding-3-small",
    )

    with pytest.raises(EmbeddingProviderError, match="dimension 1536"):
        client.embed_text("Need better alerts")
