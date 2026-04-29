from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from app.connectors.http_client import ConnectorHTTPClient
from app.connectors.product_hunt import ProductHuntConnector
from app.connectors.reddit import RedditConnector, parse_rate_limit_headers
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig


SECRET = "ph-test-token"


def test_product_hunt_http_401_maps_to_permission_limited() -> None:
    result = _collect_with_response(httpx.Response(401, json={"error": "unauthorized"}))

    assert result.status == ConnectorStatus.PERMISSION_LIMITED


def test_product_hunt_http_403_maps_to_permission_limited() -> None:
    result = _collect_with_response(httpx.Response(403, json={"error": "forbidden"}))

    assert result.status == ConnectorStatus.PERMISSION_LIMITED


def test_product_hunt_http_429_maps_to_rate_limited() -> None:
    result = _collect_with_response(
        httpx.Response(
            429,
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
            json={"error": "too many requests"},
        )
    )

    assert result.status == ConnectorStatus.RATE_LIMITED
    assert result.rate_limit_state is not None
    assert result.rate_limit_state.remaining == 0
    assert result.rate_limit_state.retry_after_seconds == 60


def test_product_hunt_graphql_quota_error_maps_to_rate_limited() -> None:
    result = _collect_with_response(
        httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"errors": [{"message": "GraphQL quota exceeded"}]},
        )
    )

    assert result.status == ConnectorStatus.RATE_LIMITED


def test_reddit_parse_rate_limit_headers() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    state, metadata = parse_rate_limit_headers(
        {
            "X-Ratelimit-Used": "3.5",
            "X-Ratelimit-Remaining": "0.0",
            "X-Ratelimit-Reset": "60",
        },
        now=now,
    )

    assert state is not None
    assert state.remaining == 0
    assert state.reset_at == now + timedelta(seconds=60)
    assert metadata == {
        "rate_limit_used": 3.5,
        "rate_limit_reset_seconds": 60.0,
    }


def test_reddit_http_429_maps_to_rate_limited_with_rate_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.reddit.com":
            return httpx.Response(
                200,
                json={"access_token": "mock-access-token"},
                request=request,
            )
        return httpx.Response(
            429,
            headers={
                "X-Ratelimit-Used": "12",
                "X-Ratelimit-Remaining": "0",
                "X-Ratelimit-Reset": "90",
                "Retry-After": "30",
            },
            json={"message": "rate limited"},
            request=request,
        )

    connector = RedditConnector(
        env={
            "REDDIT_CLIENT_ID": "client-id",
            "REDDIT_CLIENT_SECRET": "client-secret",
            "REDDIT_USER_AGENT": "SignalForge test",
        },
        transport=httpx.MockTransport(handler),
    )

    result = connector.collect_keyword_search(keywords=["wallet"])

    assert result.status == ConnectorStatus.RATE_LIMITED
    assert result.rate_limit_state is not None
    assert result.rate_limit_state.remaining == 0
    assert result.rate_limit_state.reset_at is not None
    assert result.rate_limit_state.retry_after_seconds == 30
    assert result.metadata["rate_limit_used"] == 12.0
    connector.close()


def _collect_with_response(response: httpx.Response):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        http_client=ConnectorHTTPClient(
            timeout=5.0,
            transport=httpx.MockTransport(handler),
            body_excerpt_chars=65536,
        ),
    )
    return connector.collect(
        ProjectCollectionConfig(
            project_id="00000000-0000-0000-0000-000000000001",
            platform="product_hunt",
            keywords=["wallet"],
            max_items=10,
        )
    )
