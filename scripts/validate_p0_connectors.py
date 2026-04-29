#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

try:
    import httpx
    from sqlalchemy import func, select
    from sqlalchemy.exc import SQLAlchemyError
except ImportError as exc:
    print(f"FAIL: missing required dependency: {exc}")
    sys.exit(1)


ROOT = Path(__file__).resolve().parents[1]
API_ROOT_CANDIDATES = (ROOT, ROOT / "apps" / "api", Path("/app"))
for candidate in API_ROOT_CANDIDATES:
    if (candidate / "app").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


FORBIDDEN_SECRET_MARKERS = (
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
TOKEN_ENV_KEYS = (
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USER_AGENT",
    "PRODUCT_HUNT_TOKEN",
    "SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE",
    "SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE",
)
REDDIT_ENV = {
    "REDDIT_CLIENT_ID": "mock-client-id",
    "REDDIT_CLIENT_SECRET": "mock-client-secret",
    "REDDIT_USER_AGENT": "SignalForge P0 validation",
}
PRODUCT_HUNT_TEST_TOKEN = "ph-test"
PRODUCT_HUNT_ENV = {"PRODUCT_HUNT_TOKEN": PRODUCT_HUNT_TEST_TOKEN}


class ValidationFailure(Exception):
    pass


def _fail(message: str) -> None:
    raise ValidationFailure(message)


def _pass(message: str) -> None:
    print(f"PASS: {message}")


@contextmanager
def _without_real_platform_env() -> Any:
    original = {key: os.environ.get(key) for key in TOKEN_ENV_KEYS}
    for key in TOKEN_ENV_KEYS:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _assert_no_token_markers(value: Any, context: str) -> None:
    serialized = json.dumps(value, default=str).lower()
    hits = [marker for marker in FORBIDDEN_SECRET_MARKERS if marker in serialized]
    if hits:
        _fail(f"{context} contains forbidden token markers: {hits}")


def _reddit_transport(
    *,
    api_status: int = 200,
    api_payload: dict[str, Any] | list[Any] | None = None,
    api_headers: dict[str, str] | None = None,
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "www.reddit.com":
            return httpx.Response(
                200,
                json={"access_token": "mock-access-token", "token_type": "bearer"},
                request=request,
            )
        if request.headers.get("authorization") != "Bearer mock-access-token":
            return httpx.Response(401, json={"message": "missing auth"}, request=request)
        return httpx.Response(
            api_status,
            json=api_payload or _reddit_listing_payload(),
            headers=api_headers or {},
            request=request,
        )

    return httpx.MockTransport(handler)


def _product_hunt_client(
    *,
    status: int = 200,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    from app.connectors.http_client import ConnectorHTTPClient

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("authorization") != f"Bearer {PRODUCT_HUNT_TEST_TOKEN}":
            return httpx.Response(401, json={"error": "missing auth"}, request=request)
        return httpx.Response(
            status,
            json=payload or _product_hunt_payload(),
            headers=headers or {"Content-Type": "application/json"},
            request=request,
        )

    return ConnectorHTTPClient(
        timeout=5.0,
        transport=httpx.MockTransport(handler),
        body_excerpt_chars=65536,
    )


def validate_direct_connectors() -> None:
    from app.connectors.product_hunt import ProductHuntConnector
    from app.connectors.reddit import RedditConnector
    from app.connectors.types import ConnectorStatus, ProjectCollectionConfig

    reddit_config = ProjectCollectionConfig(
        project_id=uuid4(),
        platform="reddit",
        keywords=["wallet"],
        max_items=10,
    )
    product_hunt_config = ProjectCollectionConfig(
        project_id=uuid4(),
        platform="product_hunt",
        keywords=["wallet", "onboarding"],
        max_items=10,
    )

    with _without_real_platform_env():
        reddit_disabled = RedditConnector(env={}).collect(reddit_config)
        product_disabled = ProductHuntConnector(env={}).collect(product_hunt_config)
    if reddit_disabled.status.value != "disabled":
        _fail(f"Missing Reddit credentials returned {reddit_disabled.status}")
    if product_disabled.status.value != "disabled":
        _fail(f"Missing Product Hunt token returned {product_disabled.status}")
    _assert_no_token_markers(reddit_disabled.model_dump(), "missing Reddit credentials result")
    _assert_no_token_markers(product_disabled.model_dump(), "missing Product Hunt token result")
    _pass("missing Reddit/Product Hunt credentials degrade to disabled")

    reddit = RedditConnector(env=REDDIT_ENV, transport=_reddit_transport())
    reddit_result = reddit.collect_keyword_search(keywords=["wallet"], limit=5)
    reddit_comments = RedditConnector(
        env=REDDIT_ENV,
        transport=_reddit_transport(api_payload=_reddit_comments_payload()),
    ).collect_comments("startups", "post1", keywords=["slow"], limit=1)
    reddit_deleted = RedditConnector(
        env=REDDIT_ENV,
        transport=_reddit_transport(api_payload=_reddit_deleted_payload()),
    ).collect_keyword_search(keywords=["deleted"], limit=5)
    reddit.close()

    if reddit_result.status != ConnectorStatus.SUCCESS or not reddit_result.items:
        _fail(f"mocked Reddit keyword search failed: {reddit_result.status}")
    if reddit_result.items[0].platform != "reddit" or not reddit_result.items[0].source_url:
        _fail("mocked Reddit normalized item is missing platform/source_url")
    if reddit_comments.status != ConnectorStatus.SUCCESS or not reddit_comments.items:
        _fail("mocked Reddit comments normalization failed")
    if not reddit_deleted.items or reddit_deleted.items[0].deleted_at_source is not True:
        _fail("mocked Reddit deleted item was not marked deleted_at_source")
    deleted_serialized = json.dumps(reddit_deleted.items[0].model_dump(), default=str).lower()
    if "[deleted]" in deleted_serialized or "[removed]" in deleted_serialized:
        _fail("Reddit deleted/removed body leaked into normalized output")
    _assert_no_token_markers(reddit_result.model_dump(), "mocked Reddit result")
    _pass("mocked Reddit keyword/comments/deleted normalization passes")

    product_hunt = ProductHuntConnector(
        env=PRODUCT_HUNT_ENV,
        http_client=_product_hunt_client(),
    )
    product_result = product_hunt.collect(product_hunt_config)
    if product_result.status != ConnectorStatus.SUCCESS or len(product_result.items) < 3:
        _fail(f"mocked Product Hunt normalization failed: {product_result.status}")
    if {item.platform for item in product_result.items} != {"product_hunt"}:
        _fail("Product Hunt normalized items have wrong platform")
    if any(not item.source_url for item in product_result.items):
        _fail("Product Hunt normalized item is missing source_url")
    _assert_no_token_markers(product_result.model_dump(), "mocked Product Hunt result")
    _pass("mocked Product Hunt product/comment normalization passes")

    product_no_headers = ProductHuntConnector(
        env=PRODUCT_HUNT_ENV,
        http_client=_product_hunt_client(headers={"Content-Type": "application/json"}),
    ).collect(product_hunt_config)
    if product_no_headers.status != ConnectorStatus.SUCCESS:
        _fail("Product Hunt missing rate headers incorrectly failed connector")
    _pass("Product Hunt missing rate headers do not fail connector")


def validate_status_mapping() -> None:
    from app.connectors.product_hunt import ProductHuntConnector
    from app.connectors.reddit import RedditConnector
    from app.connectors.types import ConnectorStatus, ProjectCollectionConfig

    config = ProjectCollectionConfig(project_id=uuid4(), platform="product_hunt", keywords=["wallet"], max_items=10)
    for status_code in (401, 403):
        result = ProductHuntConnector(
            env=PRODUCT_HUNT_ENV,
            http_client=_product_hunt_client(status=status_code, payload={"error": "auth"}),
        ).collect(config)
        if result.status != ConnectorStatus.PERMISSION_LIMITED:
            _fail(f"Product Hunt HTTP {status_code} returned {result.status}")

    product_rate = ProductHuntConnector(
        env=PRODUCT_HUNT_ENV,
        http_client=_product_hunt_client(
            status=429,
            payload={"error": "too many requests"},
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
        ),
    ).collect(config)
    if product_rate.status != ConnectorStatus.RATE_LIMITED:
        _fail(f"Product Hunt 429 returned {product_rate.status}")

    product_quota = ProductHuntConnector(
        env=PRODUCT_HUNT_ENV,
        http_client=_product_hunt_client(status=200, payload={"errors": [{"message": "GraphQL quota exceeded"}]}),
    ).collect(config)
    if product_quota.status != ConnectorStatus.RATE_LIMITED:
        _fail(f"Product Hunt quota error returned {product_quota.status}")

    reddit_config = ProjectCollectionConfig(project_id=uuid4(), platform="reddit", keywords=["wallet"], max_items=10)
    for status_code in (401, 403):
        reddit_result = RedditConnector(
            env=REDDIT_ENV,
            transport=_reddit_transport(api_status=status_code, api_payload={"message": "auth"}),
        ).collect(reddit_config)
        if reddit_result.status != ConnectorStatus.PERMISSION_LIMITED:
            _fail(f"Reddit HTTP {status_code} returned {reddit_result.status}")

    reddit_rate = RedditConnector(
        env=REDDIT_ENV,
        transport=_reddit_transport(
            api_status=429,
            api_payload={"message": "rate limit"},
            api_headers={
                "X-Ratelimit-Used": "9",
                "X-Ratelimit-Remaining": "0",
                "X-Ratelimit-Reset": "30",
                "Retry-After": "15",
            },
        ),
    ).collect(reddit_config)
    if reddit_rate.status != ConnectorStatus.RATE_LIMITED:
        _fail(f"Reddit 429 returned {reddit_rate.status}")
    if reddit_rate.rate_limit_state is None or reddit_rate.rate_limit_state.remaining != 0:
        _fail("Reddit 429 did not expose safe rate limit state")

    _pass("P0 connector permission/rate-limit mappings pass")


def validate_registry() -> None:
    from app.connectors.disabled import DisabledConnector
    from app.connectors.product_hunt import ProductHuntConnector
    from app.connectors.reddit import RedditConnector
    from app.connectors.registry import registry

    if not isinstance(registry.get("reddit"), RedditConnector):
        _fail("registry did not return RedditConnector")
    if not isinstance(registry.get("product_hunt"), ProductHuntConnector):
        _fail("registry did not return ProductHuntConnector")
    for platform in ("x", "discord"):
        if not isinstance(registry.get(platform), DisabledConnector):
            _fail(f"registry did not keep {platform} disabled")
    _pass("registry returns P0 connectors and keeps x/discord disabled")


def _count(db: Any, model: Any, *criteria: Any) -> int:
    statement = select(func.count()).select_from(model)
    for criterion in criteria:
        statement = statement.where(criterion)
    return int(db.scalar(statement) or 0)


def _create_project() -> UUID:
    from app.db.models import Keyword, Project
    from app.db.session import SessionLocal

    if SessionLocal is None:
        _fail("DATABASE_URL is not configured")

    with SessionLocal() as db:
        project = Project(
            name=f"P0 Connector Validation {uuid4()}",
            description="Temporary project created by validate_p0_connectors.py",
            platforms_enabled={"reddit": True, "product_hunt": True},
            collection_frequency="manual",
        )
        db.add(project)
        db.flush()
        db.add_all(
            [
                Keyword(project_id=project.id, keyword="wallet", keyword_type="main", language="en"),
                Keyword(project_id=project.id, keyword="onboarding", keyword_type="related", language="en"),
            ]
        )
        db.commit()
        return project.id


def _delete_project(project_id: UUID) -> None:
    from app.db.models import Project
    from app.db.session import SessionLocal

    if SessionLocal is None:
        return

    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is not None:
            db.delete(project)
            db.commit()


def validate_executor_modes(no_token_leak: bool) -> None:
    from app.db.models import Cluster, CollectionJob, CollectionLog, Opportunity, RawItem, Signal
    from app.db.session import SessionLocal
    from app.services.collection_executor import execute_collection

    if SessionLocal is None:
        _fail("DATABASE_URL is not configured")

    project_id = _create_project()
    try:
        with SessionLocal() as db, _without_real_platform_env():
            before_counts = {
                "signals": _count(db, Signal),
                "clusters": _count(db, Cluster),
                "opportunities": _count(db, Opportunity),
            }

            for mode, expected_platforms in {
                "reddit": {"reddit"},
                "product_hunt": {"product_hunt"},
                "p0_real": {"reddit", "product_hunt"},
            }.items():
                before_raw_items = _count(db, RawItem, RawItem.project_id == project_id)
                job = execute_collection(db, project_id=project_id, execution_mode=mode)
                logs = list(
                    db.scalars(
                        select(CollectionLog)
                        .where(CollectionLog.job_id == job.id)
                        .order_by(CollectionLog.platform.asc())
                    )
                )
                platforms = {log.platform for log in logs}
                if expected_platforms != platforms:
                    _fail(f"{mode} wrote logs for wrong platforms: {platforms}")
                if job.status != "success":
                    _fail(f"{mode} missing-token job returned {job.status}, expected success")
                if any(log.status != "disabled" for log in logs):
                    _fail(f"{mode} missing-token logs were not disabled: {[log.status for log in logs]}")
                if _count(db, RawItem, RawItem.project_id == project_id) != before_raw_items:
                    _fail(f"{mode} missing-token job wrote raw_items")

                if no_token_leak:
                    _assert_no_token_markers(
                        {
                            "job": {
                                "status": job.status,
                                "error_summary": job.error_summary,
                            },
                            "logs": [
                                {
                                    "platform": log.platform,
                                    "status": log.status,
                                    "error_message": log.error_message,
                                    "items_collected": log.items_collected,
                                    "items_inserted": log.items_inserted,
                                    "items_skipped": log.items_skipped,
                                }
                                for log in logs
                            ],
                        },
                        f"{mode} executor logs",
                    )

                if (
                    _count(db, Signal) != before_counts["signals"]
                    or _count(db, Cluster) != before_counts["clusters"]
                    or _count(db, Opportunity) != before_counts["opportunities"]
                ):
                    _fail(f"{mode} created signals, clusters, or opportunities")
            _pass("executor modes reddit/product_hunt/p0_real degrade safely without tokens")

            p0_jobs = list(
                db.scalars(
                    select(CollectionJob)
                    .where(CollectionJob.project_id == project_id)
                    .order_by(CollectionJob.created_at.asc())
                )
            )
            if len(p0_jobs) != 3:
                _fail(f"expected 3 P0 validation jobs, found {len(p0_jobs)}")
            _pass("P0 connector jobs/logs are written without pipeline side effects")
    except SQLAlchemyError as exc:
        _fail(f"database validation failed: {exc}")
    finally:
        _delete_project(project_id)


def _reddit_listing_payload() -> dict[str, Any]:
    return {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "post1",
                        "name": "t3_post1",
                        "author": "alice",
                        "title": "Wallet onboarding",
                        "selftext": "Users need faster wallet setup",
                        "permalink": "/r/startups/comments/post1/wallet_onboarding/",
                        "score": 12,
                        "num_comments": 3,
                    },
                }
            ]
        }
    }


def _reddit_comments_payload() -> list[dict[str, Any]]:
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
                            "body": "The onboarding is slow",
                            "permalink": "/r/startups/comments/post1/_/comment1/",
                            "score": 4,
                        },
                    }
                ]
            }
        },
    ]


def _reddit_deleted_payload() -> dict[str, Any]:
    return {
        "data": {
            "children": [
                {
                    "kind": "t1",
                    "data": {
                        "id": "deleted1",
                        "name": "t1_deleted1",
                        "author": "deleted-user",
                        "body": "[deleted]",
                        "permalink": "/r/startups/comments/post1/_/deleted1/",
                        "score": 0,
                    },
                }
            ]
        }
    }


def _product_hunt_payload() -> dict[str, Any]:
    return {
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
                            "user": {"id": "user-1", "username": "maker"},
                            "products": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "product-1",
                                            "slug": "launch-wallet",
                                            "name": "Launch Wallet",
                                            "tagline": "Wallet analytics",
                                            "url": "https://www.producthunt.com/products/launch-wallet",
                                        }
                                    }
                                ]
                            },
                            "comments": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "comment-1",
                                            "body": "The onboarding checklist needs clearer wallet setup steps.",
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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 4 P0 connectors without real platform calls.")
    parser.add_argument("--no-token-leak", action="store_true", help="Run stricter serialized result/log leak checks.")
    args = parser.parse_args()

    try:
        validate_registry()
        validate_direct_connectors()
        validate_status_mapping()
        validate_executor_modes(no_token_leak=args.no_token_leak)
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    except Exception as exc:
        print(f"FAIL: unexpected validation error: {exc}")
        return 1

    print("PASS: P0 connector validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
