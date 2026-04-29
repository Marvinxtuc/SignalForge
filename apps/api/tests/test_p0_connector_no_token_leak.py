from __future__ import annotations

import json

import httpx

from app.connectors.http_client import (
    ConnectorHTTPClient,
    redact_text,
    sanitize_for_logging,
    sanitize_raw_payload,
)
from app.connectors.types import ConnectorResult, ConnectorStatus, NormalizedRawItem


FORBIDDEN_MARKERS = (
    "authorization",
    "bearer",
    "access_token",
    "refresh_token",
    "client_secret",
    "reddit_client_secret",
    "product_hunt_token",
    "request_headers",
    "request object",
)


def test_redaction_removes_token_like_values_from_logs() -> None:
    secret = "ph-test-token"
    value = {
        "message": f"Authorization: Bearer {secret}",
        "access_token": secret,
        "nested": {
            "client_secret": "reddit_secret_1234567890abcdef",
            "safe": "kept",
        },
    }

    sanitized = sanitize_for_logging(value, secrets=(secret,))
    serialized = json.dumps(sanitized).lower()

    assert "safe" in serialized
    assert secret not in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_raw_payload_sanitizer_does_not_keep_request_or_auth_material() -> None:
    raw_payload = {
        "status": 200,
        "request_headers": {"Authorization": "Bearer secret-value"},
        "request": {"method": "GET", "headers": {"Authorization": "Bearer secret-value"}},
        "response": {"content-type": "application/json"},
        "body": {"PRODUCT_HUNT_TOKEN": "secret-value"},
    }

    sanitized = sanitize_raw_payload(raw_payload, secrets=("secret-value",))
    serialized = json.dumps(sanitized).lower()

    assert "status" in serialized
    assert "content-type" in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_http_client_mocked_transport_snapshot_does_not_leak_authorization() -> None:
    secret = "ph-test-token"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == f"Bearer {secret}"
        return httpx.Response(
            200,
            headers={
                "Authorization": f"Bearer {secret}",
                "Content-Type": "application/json",
                "X-RateLimit-Remaining": "10",
            },
            json={
                "ok": True,
                "echo": f"Bearer {secret}",
                "plain_echo": secret,
                "access_token": secret,
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)
    with ConnectorHTTPClient(timeout=5.0, transport=transport) as client:
        snapshot = client.request(
            "GET",
            "https://example.test/product-hunt",
            authorization=f"Bearer {secret}",
        )

    serialized = json.dumps(snapshot.model_dump()).lower()

    assert snapshot.status_code == 200
    assert snapshot.headers["content-type"] == "application/json"
    assert snapshot.headers["x-ratelimit-remaining"] == "10"
    assert "authorization" not in snapshot.headers
    assert not hasattr(snapshot, "request")
    assert secret not in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_redact_text_removes_secret_words_and_values() -> None:
    text = (
        "PRODUCT_HUNT_TOKEN=ph-test-token "
        "refresh_token=rt-test-token"
    )

    redacted = redact_text(text).lower()

    assert "[redacted]" in redacted
    assert "product_hunt_token" not in redacted
    assert "refresh_token" not in redacted
    assert "ph-test-token" not in redacted


def test_connector_result_sanitizes_error_message_and_metadata() -> None:
    secret = "ph-test-token"

    result = ConnectorResult(
        platform="product_hunt",
        status=ConnectorStatus.FAILED,
        error_message=f"Authorization Bearer {secret}",
        metadata={
            "access_token": secret,
            "safe": f"Bearer {secret}",
        },
    )
    serialized = json.dumps(result.model_dump()).lower()

    assert secret not in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized


def test_disabled_reddit_result_does_not_expose_secret_env_marker() -> None:
    from app.connectors.reddit import RedditConnector
    from app.connectors.types import ProjectCollectionConfig

    result = RedditConnector(env={}).collect(
        ProjectCollectionConfig(
            project_id="00000000-0000-0000-0000-000000000001",
            platform="reddit",
            keywords=["wallet"],
        )
    )
    serialized = json.dumps(result.model_dump()).lower()

    assert result.status == ConnectorStatus.DISABLED
    assert "reddit_client_secret" not in serialized
    assert "client_secret" not in serialized
    assert "bearer" not in serialized


def test_normalized_raw_item_sanitizes_raw_payload() -> None:
    secret = "reddit-test-token"

    item = NormalizedRawItem(
        platform="reddit",
        platform_item_id="abc",
        source_url="https://example.test/item/abc",
        raw_payload={
            "request": {"headers": {"Authorization": f"Bearer {secret}"}},
            "client_secret": secret,
            "safe": f"Bearer {secret}",
        },
    )
    serialized = json.dumps(item.model_dump()).lower()

    assert secret not in serialized
    for marker in FORBIDDEN_MARKERS:
        assert marker not in serialized
