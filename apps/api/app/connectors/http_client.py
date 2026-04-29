from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

import httpx

from app.connectors.types import HTTPResponseSnapshot


DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_BODY_EXCERPT_CHARS = 512
SAFE_RESPONSE_HEADERS = {
    "cache-control",
    "content-language",
    "content-length",
    "content-type",
    "date",
    "etag",
    "expires",
    "last-modified",
    "retry-after",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
}
SENSITIVE_KEY_PARTS = {
    "authorization",
    "bearer",
    "token",
    "secret",
    "access_token",
    "refresh_token",
    "client_secret",
    "reddit_client_secret",
    "product_hunt_token",
    "request",
    "request_headers",
    "request_object",
}
SENSITIVE_WORD_PATTERN = re.compile(
    r"(?i)\b("
    r"authorization|bearer_token|bearer|access_token|refresh_token|client_secret|"
    r"reddit_client_secret|product_hunt_token|token|secret"
    r")\b"
)
BEARER_VALUE_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
ASSIGNMENT_SECRET_PATTERN = re.compile(
    r"(?i)\b(?:authorization|access_token|refresh_token|client_secret|token|secret)"
    r"\s*[:=]\s*['\"]?[^,'\"\s)}\]]+"
)
TOKEN_LIKE_PATTERN = re.compile(
    r"(?<![/:])(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9._~+=-]{32,}(?![/:])"
)


class ConnectorHTTPClient:
    def __init__(
        self,
        *,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
        body_excerpt_chars: int = DEFAULT_BODY_EXCERPT_CHARS,
    ) -> None:
        if timeout is None:
            raise ValueError("timeout is required")
        if body_excerpt_chars < 0:
            raise ValueError("body_excerpt_chars must be non-negative")

        self._timeout = timeout
        self._body_excerpt_chars = body_excerpt_chars
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def request(
        self,
        method: str,
        url: str,
        *,
        authorization: str | None = None,
        headers: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> HTTPResponseSnapshot:
        request_headers = _build_request_headers(
            headers=headers,
            authorization=authorization,
        )
        response = self._client.request(
            method,
            url,
            headers=request_headers,
            timeout=self._timeout,
            **kwargs,
        )
        return safe_response_snapshot(
            response,
            max_body_chars=self._body_excerpt_chars,
            secrets=_authorization_secrets(authorization),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ConnectorHTTPClient:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


def _build_request_headers(
    *,
    headers: Mapping[str, str] | None,
    authorization: str | None,
) -> dict[str, str]:
    request_headers = dict(headers or {})
    if any(key.lower() == "authorization" for key in request_headers):
        raise ValueError("authorization must be passed with the authorization argument")
    if authorization:
        request_headers["Authorization"] = authorization
    return request_headers


def safe_response_snapshot(
    response: httpx.Response,
    *,
    max_body_chars: int = DEFAULT_BODY_EXCERPT_CHARS,
    secrets: tuple[str, ...] = (),
) -> HTTPResponseSnapshot:
    safe_headers = {
        key.lower(): redact_text(value, secrets=secrets)
        for key, value in response.headers.items()
        if key.lower() in SAFE_RESPONSE_HEADERS
    }
    body_excerpt = _safe_body_excerpt(
        response,
        max_body_chars=max_body_chars,
        secrets=secrets,
    )
    return HTTPResponseSnapshot(
        status_code=response.status_code,
        headers=safe_headers,
        body_excerpt=body_excerpt,
    )


def sanitize_raw_payload(value: Any, *, secrets: tuple[str, ...] = ()) -> dict[str, Any]:
    sanitized = sanitize_for_logging(value, secrets=secrets)
    if isinstance(sanitized, dict):
        return sanitized
    return {"value": sanitized}


def sanitize_for_logging(value: Any, *, secrets: tuple[str, ...] = ()) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            if _is_sensitive_key(key_text):
                continue
            sanitized[redact_text(key_text, secrets=secrets)] = sanitize_for_logging(
                child,
                secrets=secrets,
            )
        return sanitized
    if isinstance(value, list | tuple | set):
        return [sanitize_for_logging(item, secrets=secrets) for item in value]
    if isinstance(value, bytes):
        return redact_text(value.decode("utf-8", errors="replace"), secrets=secrets)
    if isinstance(value, str):
        return redact_text(value, secrets=secrets)
    return value


def redact_text(value: str, *, secrets: tuple[str, ...] = ()) -> str:
    redacted = value
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    redacted = BEARER_VALUE_PATTERN.sub("[REDACTED]", redacted)
    redacted = ASSIGNMENT_SECRET_PATTERN.sub("[REDACTED]", redacted)
    redacted = TOKEN_LIKE_PATTERN.sub("[REDACTED]", redacted)
    redacted = SENSITIVE_WORD_PATTERN.sub("[REDACTED]", redacted)
    return redacted


def _safe_body_excerpt(
    response: httpx.Response,
    *,
    max_body_chars: int,
    secrets: tuple[str, ...],
) -> str | None:
    if max_body_chars == 0:
        return None

    text = response.text
    if _looks_like_json(response):
        try:
            text = json.dumps(
                sanitize_for_logging(response.json(), secrets=secrets),
                ensure_ascii=True,
                sort_keys=True,
            )
        except ValueError:
            pass

    return redact_text(text[:max_body_chars], secrets=secrets)


def _looks_like_json(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    return "json" in content_type.lower()


def _authorization_secrets(authorization: str | None) -> tuple[str, ...]:
    if not authorization:
        return ()

    parts = [authorization]
    scheme, _, credential = authorization.partition(" ")
    if scheme.lower() == "bearer" and credential:
        parts.append(credential)
    return tuple(parts)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)
