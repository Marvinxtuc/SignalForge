from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector
from app.connectors.credential_resolver import (
    real_platform_smoke_enabled,
    resolve_connector_credentials,
)
from app.connectors.http_client import ConnectorHTTPClient
from app.connectors.product_hunt_queries import (
    PRODUCT_HUNT_GRAPHQL_ENDPOINT,
    build_posts_search_query,
)
from app.connectors.types import (
    ConnectorResult,
    ConnectorStatus,
    NormalizedRawItem,
    ProjectCollectionConfig,
    RateLimitState,
    ResolvedConnectorCredentials,
)


PLATFORM = "product_hunt"
REQUEST_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
PRODUCT_HUNT_BODY_EXCERPT_CHARS = 1_048_576
PERMISSION_ERROR_MARKERS = (
    "permission",
    "permissions",
    "scope",
    "scopes",
    "forbidden",
    "unauthorized",
    "not authorized",
    "access denied",
)
RATE_LIMIT_ERROR_MARKERS = (
    "rate limit",
    "rate limited",
    "rate_limit",
    "ratelimit",
    "quota",
    "too many requests",
    "throttled",
)
SCHEMA_ERROR_MARKERS = (
    "cannot query field",
    "unknown argument",
    "unknown field",
    "field undefined",
    "validation error",
    "parse error",
    "syntax error",
)


class ProductHuntConnector(BaseConnector):
    platform = PLATFORM

    def __init__(
        self,
        *,
        credentials: ResolvedConnectorCredentials | None = None,
        env: Mapping[str, str] | None = None,
        http_client: ConnectorHTTPClient | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        super().__init__(self.platform)
        self._credentials = credentials
        self._env = env
        self._http_client = http_client
        self._transport = transport

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        credentials = self._credentials or resolve_connector_credentials(
            self.platform,
            env=self._env,
        )
        if credentials.is_disabled:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.DISABLED,
                error_message=credentials.reason,
                metadata=credentials.safe_metadata(),
            )

        authorization = credentials.get_authorization_header()
        if not authorization:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.DISABLED,
                error_message="missing_required_env",
                metadata=credentials.safe_metadata(),
            )

        if (
            self._http_client is None
            and self._transport is None
            and not real_platform_smoke_enabled(self._env)
        ):
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.DISABLED,
                error_message=(
                    "product_hunt connector real network access is disabled; "
                    "set SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true for manual smoke"
                ),
                metadata=credentials.safe_metadata(),
            )

        payload = build_posts_search_query(
            keywords=config.keywords,
            first=config.max_items,
        )
        try:
            response = self._client().request(
                "POST",
                PRODUCT_HUNT_GRAPHQL_ENDPOINT,
                authorization=authorization,
                headers=REQUEST_HEADERS,
                json=payload,
            )
        except httpx.HTTPError as exc:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.FAILED,
                error_message=str(exc),
                metadata=credentials.safe_metadata(),
            )

        rate_limit_state = _rate_limit_state_from_headers(response.headers)
        if response.status_code in {401, 403}:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.PERMISSION_LIMITED,
                error_message=f"Product Hunt HTTP {response.status_code}",
                rate_limit_state=rate_limit_state,
                metadata=credentials.safe_metadata(),
            )
        if response.status_code == 429:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.RATE_LIMITED,
                error_message="Product Hunt rate limit reached",
                rate_limit_state=rate_limit_state,
                metadata=credentials.safe_metadata(),
            )
        if response.status_code >= 400:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.FAILED,
                error_message=f"Product Hunt HTTP {response.status_code}",
                rate_limit_state=rate_limit_state,
                metadata=credentials.safe_metadata(),
            )

        body = _parse_json_body(response.body_excerpt)
        if body is None:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.FAILED,
                error_message="Product Hunt returned invalid JSON",
                rate_limit_state=rate_limit_state,
                metadata=credentials.safe_metadata(),
            )

        errors = body.get("errors")
        if errors:
            status = _status_from_graphql_errors(errors)
            return ConnectorResult(
                platform=self.platform,
                status=status,
                error_message=_graphql_error_summary(errors),
                rate_limit_state=rate_limit_state,
                metadata=credentials.safe_metadata(),
            )

        data = body.get("data")
        if not isinstance(data, Mapping):
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.FAILED,
                error_message="Product Hunt response missing data",
                rate_limit_state=rate_limit_state,
                metadata=credentials.safe_metadata(),
            )

        items, skipped = normalize_product_hunt_data(data, config=config)
        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.SUCCESS,
            items=items,
            items_collected=len(items),
            items_skipped=skipped,
            rate_limit_state=rate_limit_state,
            metadata={
                **credentials.safe_metadata(),
                "source": "product_hunt_graphql",
            },
        )

    def _client(self) -> ConnectorHTTPClient:
        if self._http_client is not None:
            return self._http_client
        self._http_client = ConnectorHTTPClient(
            timeout=10.0,
            transport=self._transport,
            body_excerpt_chars=PRODUCT_HUNT_BODY_EXCERPT_CHARS,
        )
        return self._http_client


def normalize_product_hunt_data(
    data: Mapping[str, Any],
    *,
    config: ProjectCollectionConfig,
) -> tuple[list[NormalizedRawItem], int]:
    items: list[NormalizedRawItem] = []
    seen_ids: set[str] = set()
    skipped = 0

    for post in _post_nodes(data):
        post_item = _normalize_post(post, config=config)
        if post_item is None:
            skipped += 1
        else:
            _append_unique(items, seen_ids, post_item)

        post_url = post_item.source_url if post_item is not None else _source_url(post, "post")
        for product in _nested_product_nodes(post):
            product_item = _normalize_product(product, config=config)
            if product_item is None:
                skipped += 1
            else:
                _append_unique(items, seen_ids, product_item)

        for comment in _nested_comment_nodes(post):
            comment_item = _normalize_comment(comment, config=config, post_url=post_url)
            if comment_item is None:
                skipped += 1
            else:
                _append_unique(items, seen_ids, comment_item)

    for product in _product_nodes(data):
        product_item = _normalize_product(product, config=config)
        if product_item is None:
            skipped += 1
        else:
            _append_unique(items, seen_ids, product_item)

    for comment in _comment_nodes(data):
        comment_item = _normalize_comment(comment, config=config, post_url=None)
        if comment_item is None:
            skipped += 1
        else:
            _append_unique(items, seen_ids, comment_item)

    return items, skipped


def _normalize_post(
    node: Mapping[str, Any],
    *,
    config: ProjectCollectionConfig,
) -> NormalizedRawItem | None:
    node_id = _safe_str(node.get("id"))
    source_url = _source_url(node, "post")
    if not node_id or not source_url:
        return None

    name = _safe_str(node.get("name"))
    text = _join_text(
        name,
        _safe_str(node.get("tagline")),
        _safe_str(node.get("description")),
    )
    if _is_excluded(text, config.exclude_keywords):
        return None

    keyword_hits = _keyword_hits(text, config.keywords)
    return NormalizedRawItem(
        platform=PLATFORM,
        platform_item_id=f"post:{node_id}",
        source_url=source_url,
        author_hash=_author_hash(node.get("user")),
        content_text=text,
        content_excerpt=_excerpt(text),
        normalized_text=text.lower() if text else None,
        engagement={
            "votes": _safe_int(node.get("votesCount") or node.get("votes_count")),
            "comments": _safe_int(node.get("commentsCount") or node.get("comments_count")),
        },
        keyword_hits=keyword_hits,
        raw_payload=_safe_raw_payload(
            item_type="post",
            node_id=node_id,
            keyword_hits=keyword_hits,
            display_name=name,
            counts={
                "votes": _safe_int(node.get("votesCount") or node.get("votes_count")),
                "comments": _safe_int(node.get("commentsCount") or node.get("comments_count")),
            },
        ),
        created_at_source=_parse_datetime(node.get("createdAt") or node.get("created_at")),
    )


def _normalize_product(
    node: Mapping[str, Any],
    *,
    config: ProjectCollectionConfig,
) -> NormalizedRawItem | None:
    node_id = _safe_str(node.get("id"))
    source_url = _source_url(node, "product")
    if not node_id or not source_url:
        return None

    name = _safe_str(node.get("name"))
    text = _join_text(
        name,
        _safe_str(node.get("tagline")),
        _safe_str(node.get("description")),
    )
    if _is_excluded(text, config.exclude_keywords):
        return None

    keyword_hits = _keyword_hits(text, config.keywords)
    return NormalizedRawItem(
        platform=PLATFORM,
        platform_item_id=f"product:{node_id}",
        source_url=source_url,
        content_text=text,
        content_excerpt=_excerpt(text),
        normalized_text=text.lower() if text else None,
        keyword_hits=keyword_hits,
        raw_payload=_safe_raw_payload(
            item_type="product",
            node_id=node_id,
            keyword_hits=keyword_hits,
            display_name=name,
            counts={},
        ),
    )


def _normalize_comment(
    node: Mapping[str, Any],
    *,
    config: ProjectCollectionConfig,
    post_url: str | None,
) -> NormalizedRawItem | None:
    node_id = _safe_str(node.get("id"))
    source_url = _source_url(node, "comment", fallback_url=post_url)
    if not node_id or not source_url:
        return None

    text = _safe_str(node.get("body") or node.get("content") or node.get("text"))
    if _is_excluded(text, config.exclude_keywords):
        return None

    keyword_hits = _keyword_hits(text, config.keywords)
    return NormalizedRawItem(
        platform=PLATFORM,
        platform_item_id=f"comment:{node_id}",
        source_url=source_url,
        author_hash=_author_hash(node.get("user")),
        content_text=text,
        content_excerpt=_excerpt(text),
        normalized_text=text.lower() if text else None,
        engagement={"votes": _safe_int(node.get("votesCount") or node.get("votes_count"))},
        keyword_hits=keyword_hits,
        raw_payload=_safe_raw_payload(
            item_type="comment",
            node_id=node_id,
            keyword_hits=keyword_hits,
            display_name=None,
            counts={"votes": _safe_int(node.get("votesCount") or node.get("votes_count"))},
        ),
        created_at_source=_parse_datetime(node.get("createdAt") or node.get("created_at")),
    )


def _post_nodes(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    nodes = _connection_nodes(data.get("posts"))
    post = data.get("post")
    if isinstance(post, Mapping):
        nodes.append(post)
    nodes.extend(_typed_search_nodes(data, {"Post"}))
    return nodes


def _product_nodes(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    nodes = _connection_nodes(data.get("products"))
    product = data.get("product")
    if isinstance(product, Mapping):
        nodes.append(product)
    nodes.extend(_typed_search_nodes(data, {"Product"}))
    return nodes


def _comment_nodes(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    nodes = _connection_nodes(data.get("comments"))
    comment = data.get("comment")
    if isinstance(comment, Mapping):
        nodes.append(comment)
    nodes.extend(_typed_search_nodes(data, {"Comment"}))
    return nodes


def _nested_product_nodes(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    products = node.get("products")
    if isinstance(products, list):
        return [product for product in products if isinstance(product, Mapping)]
    return _connection_nodes(products)


def _nested_comment_nodes(node: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    comments = node.get("comments")
    if isinstance(comments, list):
        return [comment for comment in comments if isinstance(comment, Mapping)]
    return _connection_nodes(comments)


def _typed_search_nodes(
    data: Mapping[str, Any],
    typenames: set[str],
) -> list[Mapping[str, Any]]:
    nodes = []
    for node in _connection_nodes(data.get("search")):
        typename = _safe_str(node.get("__typename"))
        if typename in typenames:
            nodes.append(node)
    return nodes


def _connection_nodes(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if isinstance(value.get("nodes"), list):
            return [node for node in value["nodes"] if isinstance(node, Mapping)]
        if isinstance(value.get("edges"), list):
            nodes: list[Mapping[str, Any]] = []
            for edge in value["edges"]:
                if isinstance(edge, Mapping) and isinstance(edge.get("node"), Mapping):
                    nodes.append(edge["node"])
            return nodes
    if isinstance(value, list):
        return [node for node in value if isinstance(node, Mapping)]
    return []


def _append_unique(
    items: list[NormalizedRawItem],
    seen_ids: set[str],
    item: NormalizedRawItem,
) -> None:
    key = f"{item.platform}:{item.platform_item_id}"
    if key in seen_ids:
        return
    seen_ids.add(key)
    items.append(item)


def _status_from_graphql_errors(errors: Any) -> ConnectorStatus:
    messages = _graphql_error_messages(errors)
    joined = " ".join(messages).lower()
    if any(marker in joined for marker in RATE_LIMIT_ERROR_MARKERS):
        return ConnectorStatus.RATE_LIMITED
    if any(marker in joined for marker in PERMISSION_ERROR_MARKERS):
        return ConnectorStatus.PERMISSION_LIMITED
    if any(marker in joined for marker in SCHEMA_ERROR_MARKERS):
        return ConnectorStatus.FAILED
    return ConnectorStatus.FAILED


def _graphql_error_summary(errors: Any) -> str:
    messages = _graphql_error_messages(errors)
    if not messages:
        return "Product Hunt GraphQL error"
    return "; ".join(messages[:3])


def _graphql_error_messages(errors: Any) -> list[str]:
    if not isinstance(errors, list):
        return [_safe_str(errors)]
    messages = []
    for error in errors:
        if isinstance(error, Mapping):
            message = _safe_str(error.get("message"))
            code = _safe_str(error.get("code") or _nested_code(error.get("extensions")))
            messages.append(" ".join(part for part in (code, message) if part).strip())
        else:
            messages.append(_safe_str(error))
    return [message for message in messages if message]


def _nested_code(value: Any) -> str:
    if not isinstance(value, Mapping):
        return ""
    return _safe_str(value.get("code") or value.get("classification"))


def _parse_json_body(body_excerpt: str | None) -> dict[str, Any] | None:
    if not body_excerpt:
        return None
    try:
        parsed = json.loads(body_excerpt)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _rate_limit_state_from_headers(headers: Mapping[str, str]) -> RateLimitState | None:
    remaining = _safe_int(headers.get("x-ratelimit-remaining"))
    retry_after = _safe_int(headers.get("retry-after"))
    reset_at = _parse_rate_limit_reset(headers.get("x-ratelimit-reset"))
    if remaining is None and retry_after is None and reset_at is None:
        return None
    return RateLimitState(
        remaining=remaining,
        retry_after_seconds=retry_after,
        reset_at=reset_at,
    )


def _parse_rate_limit_reset(value: Any) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    if text.isdigit():
        return datetime.fromtimestamp(int(text), tz=UTC)
    return _parse_datetime(text)


def _source_url(
    node: Mapping[str, Any],
    item_type: str,
    *,
    fallback_url: str | None = None,
) -> str | None:
    for key in ("url", "productHuntUrl", "discussionUrl"):
        url = _safe_str(node.get(key))
        if url:
            return url
    slug = _safe_str(node.get("slug"))
    if slug and item_type in {"post", "product"}:
        path = "posts" if item_type == "post" else "products"
        return f"https://www.producthunt.com/{path}/{slug}"
    if item_type == "comment" and fallback_url:
        node_id = _safe_str(node.get("id"))
        return f"{fallback_url}#comment-{node_id}" if node_id else fallback_url
    return None


def _safe_raw_payload(
    *,
    item_type: str,
    node_id: str,
    keyword_hits: list[str],
    display_name: str | None,
    counts: Mapping[str, int | None],
) -> dict[str, Any]:
    competitor_names = [display_name] if display_name and keyword_hits else []
    safe_counts = {key: value for key, value in counts.items() if value is not None}
    return {
        "competitor_related": bool(competitor_names),
        "competitor_names": competitor_names,
        "demand_keywords": keyword_hits,
        "ids": {
            "product_hunt": node_id,
            "item_type": item_type,
        },
        "counts": safe_counts,
    }


def _author_hash(user: Any) -> str | None:
    if not isinstance(user, Mapping):
        return None
    user_key = _safe_str(user.get("id") or user.get("username") or user.get("name"))
    if not user_key:
        return None
    return hashlib.sha256(user_key.encode("utf-8")).hexdigest()


def _keyword_hits(text: str, keywords: list[str]) -> list[str]:
    normalized_text = text.lower()
    hits = []
    for keyword in keywords:
        normalized_keyword = keyword.strip().lower()
        if normalized_keyword and normalized_keyword in normalized_text:
            hits.append(keyword.strip())
    return hits


def _is_excluded(text: str, exclude_keywords: list[str]) -> bool:
    normalized_text = text.lower()
    return any(
        keyword.strip().lower() in normalized_text
        for keyword in exclude_keywords
        if keyword.strip()
    )


def _join_text(*parts: str) -> str:
    return "\n".join(part for part in parts if part).strip()


def _excerpt(text: str, max_chars: int = 240) -> str | None:
    if not text:
        return None
    return text[:max_chars]


def _parse_datetime(value: Any) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


__all__ = [
    "ProductHuntConnector",
    "normalize_product_hunt_data",
]
