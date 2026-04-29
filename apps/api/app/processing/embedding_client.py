from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


EMBEDDING_DIMENSION = 1536
MOCK_EMBEDDING_MODEL = "signalforge-mock-embedding-v1"


def _stable_seed(text: str, model_name: str) -> bytes:
    normalized = " ".join((text or "").strip().lower().split())
    return hashlib.sha256(f"{model_name}:{normalized}".encode("utf-8")).digest()


def deterministic_mock_embedding(
    text: str,
    *,
    dimension: int = EMBEDDING_DIMENSION,
    model_name: str = MOCK_EMBEDDING_MODEL,
) -> list[float]:
    """Generate a deterministic unit vector with stable cryptographic digests."""
    if dimension <= 0:
        raise ValueError("embedding dimension must be positive")

    seed = _stable_seed(text, model_name)
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        block = hashlib.blake2b(seed + counter.to_bytes(4, "big"), digest_size=64).digest()
        for index in range(0, len(block), 2):
            if len(values) >= dimension:
                break
            raw = int.from_bytes(block[index : index + 2], "big")
            values.append((raw / 32767.5) - 1.0)
        counter += 1

    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return [0.0] * dimension
    return [value / norm for value in values]


def validate_embedding(vector: list[float], *, dimension: int = EMBEDDING_DIMENSION) -> None:
    if len(vector) != dimension:
        raise ValueError(f"embedding must have dimension {dimension}, got {len(vector)}")
    if any(not math.isfinite(value) for value in vector):
        raise ValueError("embedding must contain only finite numeric values")


@dataclass(frozen=True)
class EmbeddingResult:
    text: str
    embedding: list[float]
    model_name: str = MOCK_EMBEDDING_MODEL


class MockEmbeddingClient:
    model_name = MOCK_EMBEDDING_MODEL
    dimension = EMBEDDING_DIMENSION

    def embed_text(self, text: str) -> EmbeddingResult:
        embedding = deterministic_mock_embedding(text, dimension=self.dimension, model_name=self.model_name)
        validate_embedding(embedding, dimension=self.dimension)
        return EmbeddingResult(text=text, embedding=embedding, model_name=self.model_name)

    def embed_many(self, texts: list[str]) -> list[EmbeddingResult]:
        return [self.embed_text(text) for text in texts]
