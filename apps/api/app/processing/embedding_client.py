from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Mapping


EMBEDDING_DIMENSION = 1536
MOCK_EMBEDDING_MODEL = "signalforge-mock-embedding-v1"
REAL_EMBEDDING_FLAG = "SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE"
REQUIRED_EMBEDDING_ENV = ("LLM_BASE_URL", "LLM_API_KEY", "EMBEDDING_MODEL")
MAX_EMBEDDING_INPUT_CHARS = 8000
MAX_EMBEDDING_RESPONSE_BYTES = 262144


class EmbeddingProviderError(RuntimeError):
    pass


def real_embedding_enabled(env: Mapping[str, str] | None = None) -> bool:
    source = env or os.environ
    return source.get(REAL_EMBEDDING_FLAG, "").strip().lower() == "true"


def missing_embedding_env(env: Mapping[str, str] | None = None) -> list[str]:
    source = env or os.environ
    return [name for name in REQUIRED_EMBEDDING_ENV if not source.get(name, "").strip()]


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
    if any(not isinstance(value, int | float) or isinstance(value, bool) or not math.isfinite(value) for value in vector):
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


class OpenAICompatibleEmbeddingClient:
    dimension = EMBEDDING_DIMENSION

    def __init__(self, *, base_url: str, api_key: str, model: str, timeout_seconds: float = 15.0) -> None:
        self.base_url = base_url.strip().rstrip("/")
        self.api_key = api_key
        self.model_name = model.strip()
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None, *, timeout_seconds: float = 15.0) -> "OpenAICompatibleEmbeddingClient":
        source = env or os.environ
        if not real_embedding_enabled(source):
            raise EmbeddingProviderError(
                "Real embedding is disabled. Set SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true to allow a provider call."
            )
        missing = missing_embedding_env(source)
        if missing:
            raise EmbeddingProviderError("Real embedding requires LLM_BASE_URL, LLM_API_KEY, and EMBEDDING_MODEL.")
        return cls(
            base_url=source["LLM_BASE_URL"],
            api_key=source["LLM_API_KEY"],
            model=source["EMBEDDING_MODEL"],
            timeout_seconds=timeout_seconds,
        )

    def embed_text(self, text: str) -> EmbeddingResult:
        safe_text = str(text or "")[:MAX_EMBEDDING_INPUT_CHARS]
        payload = {
            "model": self.model_name,
            "input": safe_text,
        }
        request = urllib.request.Request(
            _embeddings_url(self.base_url),
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310 - gated real embedding path.
                status_code = int(getattr(response, "status", 0) or 0)
                body = response.read(MAX_EMBEDDING_RESPONSE_BYTES).decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise EmbeddingProviderError(f"Embedding provider HTTP {exc.code}: {_safe_excerpt(exc.read(512))}") from exc
        except Exception as exc:
            raise EmbeddingProviderError(_redact(str(exc))) from exc

        if not 200 <= status_code < 300:
            raise EmbeddingProviderError(f"Embedding provider HTTP {status_code}: {_safe_excerpt(body)}")
        embedding = _embedding_from_response(body)
        try:
            validate_embedding(embedding, dimension=self.dimension)
        except ValueError as exc:
            raise EmbeddingProviderError(str(exc)) from exc
        return EmbeddingResult(text=text, embedding=embedding, model_name=self.model_name)

    def embed_many(self, texts: list[str]) -> list[EmbeddingResult]:
        return [self.embed_text(text) for text in texts]


def _embeddings_url(base_url: str) -> str:
    if base_url.endswith("/embeddings"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/embeddings"
    return f"{base_url}/v1/embeddings"


def _embedding_from_response(body: str) -> list[float]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise EmbeddingProviderError("Embedding provider returned invalid JSON response") from exc

    data = payload.get("data") if isinstance(payload, Mapping) else None
    if not isinstance(data, list) or not data:
        raise EmbeddingProviderError("Embedding provider response missing data")
    first = data[0]
    if not isinstance(first, Mapping):
        raise EmbeddingProviderError("Embedding provider response item is invalid")
    embedding = first.get("embedding")
    if not isinstance(embedding, list):
        raise EmbeddingProviderError("Embedding provider response missing embedding")
    return embedding


def _safe_excerpt(value: bytes | str) -> str:
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
    return _redact(text)[:500]


def _redact(text: str) -> str:
    redacted = str(text or "")
    for marker in ("Bearer ", "token", "secret", "api_key", "authorization"):
        redacted = redacted.replace(marker, "[REDACTED]")
        redacted = redacted.replace(marker.upper(), "[REDACTED]")
    return redacted
