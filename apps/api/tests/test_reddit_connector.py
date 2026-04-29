from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from app.connectors.reddit import (
    RedditConnector,
    normalize_comments_response,
    normalize_listing_response,
)
from app.connectors.reddit_query import (
    build_comments_endpoint,
    build_comments_params,
    build_keyword_search_params,
    build_keyword_search_query,
    build_subreddit_watch_endpoint,
)
from app.connectors.types import ConnectorStatus, ProjectCollectionConfig


ENV = {
    "REDDIT_CLIENT_ID": "client-id",
    "REDDIT_CLIENT_SECRET": "client-secret",
    "REDDIT_USER_AGENT": "SignalForge test",
}


def test_reddit_missing_env_returns_disabled_connector_result() -> None:
    connector = RedditConnector(env={})

    result = connector.collect(
        ProjectCollectionConfig(
            project_id=uuid4(),
            platform="reddit",
            keywords=["wallet"],
        )
    )

    assert result.status == ConnectorStatus.DISABLED
    assert result.items_collected == 0
    assert result.metadata == {
        "credential_status": "missing",
        "missing_required_env_count": 3,
    }


def test_mocked_401_and_403_return_permission_limited() -> None:
    for status_code in (401, 403):
        connector = RedditConnector(env=ENV, transport=_transport(status_code=status_code))

        result = connector.collect_keyword_search(keywords=["wallet"])

        assert result.status == ConnectorStatus.PERMISSION_LIMITED
        assert result.items == []
        connector.close()


def test_mocked_keyword_search_normalizes_items() -> None:
    connector = RedditConnector(env=ENV, transport=_transport(payload=_listing_payload()))

    result = connector.collect_keyword_search(keywords=["wallet"], limit=5)

    assert result.status == ConnectorStatus.SUCCESS
    assert result.items_collected == 1
    item = result.items[0]
    assert item.platform == "reddit"
    assert item.platform_item_id == "t3_post1"
    assert item.source_url == "https://www.reddit.com/r/startups/comments/post1/wallet_feedback/"
    assert item.author_hash
    assert "alice" not in json.dumps(item.model_dump(), default=str).lower()
    assert item.content_text == "Wallet feedback\nCheckout onboarding is confusing"
    assert item.normalized_text == "wallet feedback checkout onboarding is confusing"
    assert item.keyword_hits == ["wallet"]
    assert item.raw_payload["id"] == "post1"


def test_mocked_subreddit_watch_normalizes_items() -> None:
    connector = RedditConnector(env=ENV, transport=_transport(payload=_listing_payload()))

    result = connector.collect_subreddit_watch("r/startups", keywords=["checkout"], limit=5)

    assert result.status == ConnectorStatus.SUCCESS
    assert result.metadata["collection_kind"] == "subreddit_watch"
    assert result.items[0].keyword_hits == ["checkout"]


def test_mocked_comments_normalizes_top_n_comments() -> None:
    connector = RedditConnector(env=ENV, transport=_transport(payload=_comments_payload()))

    result = connector.collect_comments("startups", "post1", keywords=["slow"], limit=1)

    assert result.status == ConnectorStatus.SUCCESS
    assert result.items_collected == 1
    assert result.items[0].platform_item_id == "t1_comment1"
    assert result.items[0].content_text == "The onboarding is slow but fixable"
    assert result.items[0].keyword_hits == ["slow"]


def test_deleted_and_removed_content_clears_body_and_raw_payload() -> None:
    payload = {
        "data": {
            "children": [
                {
                    "kind": "t1",
                    "data": {
                        "id": "gone1",
                        "name": "t1_gone1",
                        "author": "bob",
                        "body": "[removed]",
                        "permalink": "/r/startups/comments/post1/_/gone1/",
                        "score": 1,
                    },
                }
            ]
        }
    }

    items = normalize_listing_response(payload)

    assert len(items) == 1
    item = items[0]
    assert item.deleted_at_source is True
    assert item.content_text == ""
    assert item.content_excerpt == ""
    assert item.normalized_text == ""
    serialized_payload = json.dumps(item.raw_payload).lower()
    assert "[removed]" not in serialized_payload
    assert "body" not in serialized_payload
    assert "bob" not in serialized_payload


def test_deleted_post_clears_title_selftext_and_raw_payload() -> None:
    payload = {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "deleted-post",
                        "name": "t3_deleted-post",
                        "author": "deleted-user",
                        "title": "[deleted]",
                        "selftext": "This should not remain",
                        "permalink": "/r/startups/comments/deleted-post/deleted/",
                        "score": 0,
                    },
                }
            ]
        }
    }

    items = normalize_listing_response(payload)

    assert len(items) == 1
    item = items[0]
    assert item.deleted_at_source is True
    assert item.content_text == ""
    assert item.content_excerpt == ""
    assert item.normalized_text == ""
    serialized_payload = json.dumps(item.raw_payload).lower()
    assert "[deleted]" not in serialized_payload
    assert "this should not remain" not in serialized_payload
    assert "title" not in serialized_payload
    assert "selftext" not in serialized_payload
    assert "deleted-user" not in serialized_payload


def test_reddit_query_builders() -> None:
    assert build_keyword_search_query(["wallet app", "checkout"], exclude_keywords=["hiring"]) == (
        '"wallet app" OR checkout -hiring'
    )
    assert build_keyword_search_params(["wallet"], limit=999)["limit"] == 100
    assert build_subreddit_watch_endpoint("/r/startups/") == "/r/startups/new"
    assert build_comments_endpoint("r/startups", "abc123") == "/r/startups/comments/abc123"
    assert build_comments_params(limit=0)["limit"] == 1


def test_comment_response_helper_accepts_reddit_comments_array() -> None:
    items = normalize_comments_response(_comments_payload(), limit=2)

    assert [item.platform_item_id for item in items] == ["t1_comment1", "t1_comment2"]


def _transport(
    *,
    status_code: int = 200,
    payload: dict | list | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.reddit.com":
            return httpx.Response(
                200,
                json={"access_token": "mock-access-token", "token_type": "bearer"},
                request=request,
            )
        assert request.headers["authorization"] == "Bearer mock-access-token"
        return httpx.Response(
            status_code,
            json=payload or {"data": {"children": []}},
            headers=headers or {},
            request=request,
        )

    return httpx.MockTransport(handler)


def _listing_payload() -> dict:
    return {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "post1",
                        "name": "t3_post1",
                        "author": "alice",
                        "title": "Wallet feedback",
                        "selftext": "Checkout onboarding is confusing",
                        "permalink": "/r/startups/comments/post1/wallet_feedback/",
                        "score": 42,
                        "num_comments": 7,
                        "created_utc": datetime(2026, 1, 1, tzinfo=UTC).timestamp(),
                    },
                }
            ]
        }
    }


def _comments_payload() -> list[dict]:
    return [
        {"data": {"children": []}},
        {
            "data": {
                "children": [
                    {
                        "kind": "t1",
                        "data": {
                            "id": "comment1",
                            "name": "t1_comment1",
                            "author": "commenter",
                            "body": "The onboarding is slow but fixable",
                            "permalink": "/r/startups/comments/post1/_/comment1/",
                            "score": 12,
                        },
                    },
                    {
                        "kind": "t1",
                        "data": {
                            "id": "comment2",
                            "name": "t1_comment2",
                            "author": "other-commenter",
                            "body": "Second comment",
                            "permalink": "/r/startups/comments/post1/_/comment2/",
                            "score": 3,
                        },
                    },
                ]
            }
        },
    ]
