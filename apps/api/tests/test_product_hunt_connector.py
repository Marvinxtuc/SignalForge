from __future__ import annotations

import json
from uuid import uuid4

import httpx

from app.connectors.http_client import ConnectorHTTPClient
from app.connectors.product_hunt import ProductHuntConnector
from app.connectors.product_hunt_queries import PRODUCT_HUNT_GRAPHQL_ENDPOINT
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig


SECRET = "ph-test-token"


def test_product_hunt_missing_token_returns_disabled() -> None:
    connector = ProductHuntConnector(env={})
    result = connector.collect(_config())

    assert result.status == ConnectorStatus.DISABLED
    assert result.items == []
    assert result.metadata == {
        "credential_status": "missing",
        "missing_required_env_count": 1,
    }


def test_product_hunt_posts_and_comments_are_normalized() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "POST"
        assert str(request.url) == PRODUCT_HUNT_GRAPHQL_ENDPOINT
        assert request.headers["accept"] == "application/json"
        assert request.headers["content-type"] == "application/json"
        assert request.headers["authorization"] == f"Bearer {SECRET}"
        body = json.loads(request.content)
        assert "query" in body
        assert "search:" not in body["query"]
        assert "products" not in body["query"]
        assert body["variables"] == {
            "first": 10,
            "commentsFirst": 5,
        }
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "data": {
                    "posts": {
                        "edges": [
                            {
                                "node": {
                                    "id": "post-1",
                                    "slug": "launch-wallet",
                                    "name": "Launch Wallet",
                                    "tagline": "Wallet onboarding feedback",
                                    "description": "Users want a faster onboarding flow.",
                                    "url": "https://www.producthunt.com/posts/launch-wallet",
                                    "votesCount": 42,
                                    "commentsCount": 1,
                                    "createdAt": "2026-04-01T10:00:00Z",
                                    "user": {"id": "user-1", "username": "maker"},
                                    "comments": {
                                        "edges": [
                                            {
                                                "node": {
                                                    "id": "comment-1",
                                                    "body": "The onboarding checklist needs clearer wallet setup steps.",
                                                    "createdAt": "2026-04-01T11:00:00Z",
                                                    "user": {"id": "user-2"},
                                                }
                                            }
                                        ]
                                    },
                                }
                            }
                        ]
                    }
                }
            },
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        http_client=_client(handler),
    )
    result = connector.collect(_config(keywords=["wallet", "onboarding"]))

    assert len(requests) == 1
    assert result.status == ConnectorStatus.SUCCESS
    assert result.items_collected == 2
    assert {item.platform_item_id for item in result.items} == {
        "post:post-1",
        "comment:comment-1",
    }
    assert all(item.source_url for item in result.items)
    comment = next(item for item in result.items if item.platform_item_id == "comment:comment-1")
    assert comment.source_url == "https://www.producthunt.com/posts/launch-wallet#comment-comment-1"


def test_product_hunt_missing_rate_headers_success_does_not_fail() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"data": {"posts": {"edges": []}}},
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        http_client=_client(handler),
    )
    result = connector.collect(_config())

    assert result.status == ConnectorStatus.SUCCESS
    assert result.rate_limit_state is None
    assert result.items_collected == 0


def test_product_hunt_large_success_response_is_not_truncated_before_json_parse() -> None:
    large_description = "wallet onboarding " * 5000

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "data": {
                    "posts": {
                        "edges": [
                            {
                                "node": {
                                    "id": "post-large",
                                    "slug": "large-wallet",
                                    "name": "Large Wallet",
                                    "tagline": "Wallet onboarding",
                                    "description": large_description,
                                    "url": "https://www.producthunt.com/posts/large-wallet",
                                }
                            }
                        ]
                    }
                }
            },
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        transport=httpx.MockTransport(handler),
    )
    result = connector.collect(_config())

    assert result.status == ConnectorStatus.SUCCESS
    assert result.items_collected == 1
    assert result.items[0].platform_item_id == "post:post-large"


def test_product_hunt_graphql_permission_error_maps_to_permission_limited() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"errors": [{"message": "Permission denied: missing scope"}]},
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        http_client=_client(handler),
    )
    result = connector.collect(_config())

    assert result.status == ConnectorStatus.PERMISSION_LIMITED


def test_product_hunt_graphql_schema_error_maps_to_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={"errors": [{"message": "Cannot query field bogusField on type Post"}]},
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        http_client=_client(handler),
    )
    result = connector.collect(_config())

    assert result.status == ConnectorStatus.FAILED


def test_product_hunt_raw_payload_metadata_is_safe_and_token_free() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Type": "application/json"},
            json={
                "data": {
                    "products": {
                        "edges": [
                            {
                                "node": {
                                    "id": "product-safe",
                                    "name": "Acme Wallet",
                                    "tagline": "Wallet demand tracking",
                                    "url": "https://www.producthunt.com/products/acme-wallet",
                                    "request_headers": {"Authorization": f"Bearer {SECRET}"},
                                }
                            }
                        ]
                    }
                }
            },
            request=request,
        )

    connector = ProductHuntConnector(
        env={"PRODUCT_HUNT_TOKEN": SECRET},
        http_client=_client(handler),
    )
    result = connector.collect(_config(keywords=["wallet"]))

    assert result.status == ConnectorStatus.SUCCESS
    assert len(result.items) == 1
    raw_payload = result.items[0].raw_payload
    serialized = json.dumps(raw_payload).lower()
    assert raw_payload == {
        "competitor_related": True,
        "competitor_names": ["Acme Wallet"],
        "demand_keywords": ["wallet"],
        "ids": {
            "product_hunt": "product-safe",
            "item_type": "product",
        },
        "counts": {},
    }
    assert SECRET not in serialized
    assert "authorization" not in serialized
    assert "bearer" not in serialized
    assert "token" not in serialized
    assert "request_headers" not in serialized


def _client(handler: httpx.MockTransport | httpx.SyncByteStream | object) -> ConnectorHTTPClient:
    return ConnectorHTTPClient(
        timeout=5.0,
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        body_excerpt_chars=65536,
    )


def _config(
    *,
    keywords: list[str] | None = None,
) -> ProjectCollectionConfig:
    return ProjectCollectionConfig(
        project_id=uuid4(),
        platform="product_hunt",
        keywords=keywords or ["wallet", "onboarding"],
        max_items=10,
    )
