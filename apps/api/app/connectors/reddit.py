from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.connectors.base import BaseConnector
from app.connectors.credential_resolver import (
    real_platform_smoke_enabled,
    resolve_connector_credentials,
)
from app.connectors.http_client import sanitize_raw_payload
from app.connectors.reddit_query import (
    API_BASE_URL,
    TOKEN_URL,
    build_comments_params,
    build_comments_url,
    build_keyword_search_params,
    build_keyword_search_url,
    build_subreddit_watch_params,
    build_subreddit_watch_url,
)
from app.connectors.types import (
    ConnectorResult,
    ConnectorStatus,
    HTTPResponseSnapshot,
    NormalizedRawItem,
    ProjectCollectionConfig,
    RateLimitState,
)


DELETED_MARKERS = {"[deleted]", "[removed]"}
REDDIT_WEB_BASE_URL = "https://www.reddit.com"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_ITEMS = 25


class RedditConnectorError(Exception):
    def __init__(
        self,
        status: ConnectorStatus,
        message: str,
        *,
        rate_limit_state: RateLimitState | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.rate_limit_state = rate_limit_state
        self.metadata = metadata or {}


class RedditConnector(BaseConnector):
    platform = "reddit"

    def __init__(
        self,
        *,
        env: Mapping[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT_SECONDS,
        api_base_url: str = API_BASE_URL,
        token_url: str = TOKEN_URL,
    ) -> None:
        super().__init__(self.platform)
        self._credentials = resolve_connector_credentials(self.platform, env=env)
        self._client = httpx.Client(timeout=timeout, transport=transport)
        self._transport = transport
        self._api_base_url = api_base_url
        self._token_url = token_url

    def collect(self, config: ProjectCollectionConfig) -> ConnectorResult:
        if self._credentials.is_disabled:
            return self._disabled_result()

        if not config.keywords:
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.DISABLED,
                error_message="reddit connector requires at least one keyword for collection",
                metadata=self._credentials.safe_metadata(),
            )

        return self.collect_keyword_search(
            keywords=config.keywords,
            exclude_keywords=config.exclude_keywords,
            limit=config.max_items or DEFAULT_MAX_ITEMS,
        )

    def collect_keyword_search(
        self,
        *,
        keywords: Sequence[str],
        exclude_keywords: Sequence[str] = (),
        limit: int = DEFAULT_MAX_ITEMS,
    ) -> ConnectorResult:
        return self._collect_listing(
            url=build_keyword_search_url(base_url=self._api_base_url),
            params=build_keyword_search_params(
                keywords,
                exclude_keywords=exclude_keywords,
                limit=limit,
            ),
            keywords=keywords,
            limit=limit,
            collection_kind="keyword_search",
        )

    def collect_subreddit_watch(
        self,
        subreddit: str,
        *,
        keywords: Sequence[str] = (),
        limit: int = DEFAULT_MAX_ITEMS,
        sort: str = "new",
    ) -> ConnectorResult:
        url = build_subreddit_watch_url(
            subreddit,
            sort=sort,
            base_url=self._api_base_url,
        )
        return self._collect_listing(
            url=url,
            params=build_subreddit_watch_params(limit=limit),
            keywords=keywords,
            limit=limit,
            collection_kind="subreddit_watch",
        )

    def collect_comments(
        self,
        subreddit: str,
        post_id: str,
        *,
        keywords: Sequence[str] = (),
        limit: int = 10,
    ) -> ConnectorResult:
        if self._credentials.is_disabled:
            return self._disabled_result()

        try:
            token = self._acquire_access_token()
            data, rate_limit_state, metadata = self._get_json(
                build_comments_url(subreddit, post_id, base_url=self._api_base_url),
                token=token,
                params=build_comments_params(limit=limit),
            )
            items = normalize_comments_response(data, keywords=keywords, limit=limit)
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.SUCCESS,
                items=items,
                items_collected=len(items),
                rate_limit_state=rate_limit_state,
                metadata={"collection_kind": "comments", **metadata},
            )
        except RedditConnectorError as exc:
            return self._error_result(exc)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> RedditConnector:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def _collect_listing(
        self,
        *,
        url: str,
        params: Mapping[str, str | int],
        keywords: Sequence[str],
        limit: int,
        collection_kind: str,
    ) -> ConnectorResult:
        if self._credentials.is_disabled:
            return self._disabled_result()

        try:
            token = self._acquire_access_token()
            data, rate_limit_state, metadata = self._get_json(
                url,
                token=token,
                params=params,
            )
            items = normalize_listing_response(data, keywords=keywords, limit=limit)
            return ConnectorResult(
                platform=self.platform,
                status=ConnectorStatus.SUCCESS,
                items=items,
                items_collected=len(items),
                rate_limit_state=rate_limit_state,
                metadata={"collection_kind": collection_kind, **metadata},
            )
        except RedditConnectorError as exc:
            return self._error_result(exc)

    def _acquire_access_token(self) -> str:
        client_id = self._credentials.get_client_id()
        client_secret = self._credentials.get_client_secret()
        user_agent = self._credentials.get_user_agent()
        if not client_id or not client_secret or not user_agent:
            raise RedditConnectorError(
                ConnectorStatus.DISABLED,
                "reddit connector missing required credentials",
                metadata=self._credentials.safe_metadata(),
            )

        if self._transport is None and not real_platform_smoke_enabled(self._env):
            raise RedditConnectorError(
                ConnectorStatus.DISABLED,
                "reddit connector real network access is disabled; set SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true for manual smoke",
                metadata=self._credentials.safe_metadata(),
            )

        try:
            response = self._client.post(
                self._token_url,
                auth=(client_id, client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": user_agent},
            )
        except httpx.TimeoutException as exc:
            raise RedditConnectorError(ConnectorStatus.FAILED, "reddit token request timed out") from exc
        except httpx.HTTPError as exc:
            raise RedditConnectorError(ConnectorStatus.FAILED, "reddit token request failed") from exc

        self._raise_for_status(response, operation="reddit token request")

        try:
            token = response.json().get("access_token")
        except ValueError as exc:
            raise RedditConnectorError(ConnectorStatus.FAILED, "reddit token response was not valid json") from exc

        if not isinstance(token, str) or not token.strip():
            raise RedditConnectorError(ConnectorStatus.FAILED, "reddit token response missing access token")
        return token

    def _get_json(
        self,
        url: str,
        *,
        token: str,
        params: Mapping[str, str | int],
    ) -> tuple[Any, RateLimitState | None, dict[str, Any]]:
        user_agent = self._credentials.get_user_agent()
        try:
            response = self._client.get(
                url,
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": user_agent or "SignalForge",
                },
            )
        except httpx.TimeoutException as exc:
            raise RedditConnectorError(ConnectorStatus.FAILED, "reddit api request timed out") from exc
        except httpx.HTTPError as exc:
            raise RedditConnectorError(ConnectorStatus.FAILED, "reddit api request failed") from exc

        self._raise_for_status(response, operation="reddit api request")
        rate_limit_state, metadata = parse_rate_limit_headers(response.headers)

        try:
            return response.json(), rate_limit_state, metadata
        except ValueError as exc:
            raise RedditConnectorError(
                ConnectorStatus.FAILED,
                "reddit api response was not valid json",
                rate_limit_state=rate_limit_state,
                metadata=metadata,
            ) from exc

    def _raise_for_status(self, response: httpx.Response, *, operation: str) -> None:
        if response.status_code < 400:
            return

        status = _status_for_http_code(response.status_code)
        rate_limit_state, metadata = parse_rate_limit_headers(response.headers)
        retry_after = _parse_int(response.headers.get("retry-after"))
        if retry_after is not None:
            rate_limit_state = rate_limit_state or RateLimitState()
            rate_limit_state.retry_after_seconds = retry_after

        raise RedditConnectorError(
            status,
            f"{operation} returned HTTP {response.status_code}",
            rate_limit_state=rate_limit_state,
            metadata={
                **metadata,
                "http_response": HTTPResponseSnapshot(
                    status_code=response.status_code,
                    headers=_safe_rate_headers(response.headers),
                ).model_dump(),
            },
        )

    def _disabled_result(self) -> ConnectorResult:
        return ConnectorResult(
            platform=self.platform,
            status=ConnectorStatus.DISABLED,
            error_message="reddit connector disabled: missing required REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, or REDDIT_USER_AGENT",
            metadata=self._credentials.safe_metadata(),
        )

    def _error_result(self, exc: RedditConnectorError) -> ConnectorResult:
        return ConnectorResult(
            platform=self.platform,
            status=exc.status,
            error_message=exc.message,
            rate_limit_state=exc.rate_limit_state,
            metadata={**self._credentials.safe_metadata(), **exc.metadata},
        )


def normalize_listing_response(
    payload: Any,
    *,
    keywords: Sequence[str] = (),
    limit: int = DEFAULT_MAX_ITEMS,
) -> list[NormalizedRawItem]:
    children = _listing_children(payload)
    items: list[NormalizedRawItem] = []
    for child in children:
        if len(items) >= limit:
            break
        normalized = _normalize_child(child, keywords=keywords)
        if normalized is not None:
            items.append(normalized)
    return items


def normalize_comments_response(
    payload: Any,
    *,
    keywords: Sequence[str] = (),
    limit: int = 10,
) -> list[NormalizedRawItem]:
    comments_payload = payload[1] if isinstance(payload, list) and len(payload) > 1 else payload
    children = _listing_children(comments_payload)
    items: list[NormalizedRawItem] = []
    for child in children:
        if len(items) >= limit:
            break
        if child.get("kind") != "t1":
            continue
        normalized = _normalize_child(child, keywords=keywords)
        if normalized is not None:
            items.append(normalized)
    return items


def parse_rate_limit_headers(
    headers: Mapping[str, str],
    *,
    now: datetime | None = None,
) -> tuple[RateLimitState | None, dict[str, Any]]:
    used = _parse_float(_header_value(headers, "x-ratelimit-used"))
    remaining = _parse_float(_header_value(headers, "x-ratelimit-remaining"))
    reset_seconds = _parse_float(_header_value(headers, "x-ratelimit-reset"))

    metadata: dict[str, Any] = {}
    if used is not None:
        metadata["rate_limit_used"] = used

    if remaining is None and reset_seconds is None:
        return None, metadata

    current_time = now or datetime.now(UTC)
    reset_at = None
    if reset_seconds is not None:
        reset_at = current_time + timedelta(seconds=max(0.0, reset_seconds))
        metadata["rate_limit_reset_seconds"] = reset_seconds

    return (
        RateLimitState(
            remaining=max(0, int(remaining)) if remaining is not None else None,
            reset_at=reset_at,
        ),
        metadata,
    )


def _normalize_child(
    child: Mapping[str, Any],
    *,
    keywords: Sequence[str],
) -> NormalizedRawItem | None:
    data = child.get("data")
    if not isinstance(data, Mapping):
        return None

    kind = str(child.get("kind") or data.get("kind") or "")
    item_id = _platform_item_id(kind, data)
    if not item_id:
        return None

    content_fields = _content_fields(data)
    deleted_at_source = any(_is_deleted_marker(value) for value in content_fields)
    content_text = "" if deleted_at_source else _join_content(content_fields)
    normalized_text = _normalize_text(content_text)
    raw_payload = _raw_payload(data, deleted_at_source=deleted_at_source)

    return NormalizedRawItem(
        platform="reddit",
        platform_item_id=item_id,
        source_url=_source_url(data),
        author_hash=_author_hash(data.get("author")),
        content_text=content_text,
        content_excerpt=_excerpt(content_text),
        normalized_text=normalized_text,
        engagement=_engagement(data),
        keyword_hits=_keyword_hits(content_text, keywords),
        raw_payload=raw_payload,
        deleted_at_source=deleted_at_source,
        created_at_source=_created_at(data),
    )


def _listing_children(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    data = payload.get("data")
    if not isinstance(data, Mapping):
        return []
    children = data.get("children")
    if not isinstance(children, list):
        return []
    return [child for child in children if isinstance(child, Mapping)]


def _content_fields(data: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("title", "selftext", "body"):
        value = data.get(key)
        if isinstance(value, str):
            values.append(value)
    return values


def _join_content(values: Sequence[str]) -> str:
    return "\n".join(value.strip() for value in values if value.strip())


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _excerpt(value: str, *, max_chars: int = 280) -> str:
    return value[:max_chars]


def _keyword_hits(content_text: str, keywords: Sequence[str]) -> list[str]:
    lower_content = content_text.lower()
    hits = []
    for keyword in keywords:
        normalized_keyword = keyword.strip().lower()
        if normalized_keyword and normalized_keyword in lower_content:
            hits.append(keyword)
    return hits


def _source_url(data: Mapping[str, Any]) -> str:
    permalink = data.get("permalink")
    if isinstance(permalink, str) and permalink.strip():
        if permalink.startswith("http://") or permalink.startswith("https://"):
            return permalink
        return f"{REDDIT_WEB_BASE_URL}{permalink}"

    url = data.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url

    item_id = str(data.get("name") or data.get("id") or "unknown")
    return f"{REDDIT_WEB_BASE_URL}/comments/{item_id}"


def _platform_item_id(kind: str, data: Mapping[str, Any]) -> str:
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        return name
    item_id = data.get("id")
    if isinstance(item_id, str) and item_id.strip():
        prefix = kind if kind else "reddit"
        return f"{prefix}_{item_id}"
    return ""


def _author_hash(author: Any) -> str | None:
    if not isinstance(author, str):
        return None
    normalized_author = author.strip().lower()
    if not normalized_author or _is_deleted_marker(normalized_author):
        return None
    digest = hashlib.sha256(f"reddit:{normalized_author}".encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _engagement(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "score": data.get("score"),
        "num_comments": data.get("num_comments"),
        "ups": data.get("ups"),
        "downs": data.get("downs"),
    }


def _created_at(data: Mapping[str, Any]) -> datetime | None:
    created = data.get("created_utc")
    if isinstance(created, int | float):
        return datetime.fromtimestamp(created, tz=UTC)
    return None


def _raw_payload(data: Mapping[str, Any], *, deleted_at_source: bool) -> dict[str, Any]:
    blocked_keys = {
        "author",
        "author_fullname",
        "secure_media",
        "media",
    }
    if deleted_at_source:
        blocked_keys.update({"body", "selftext", "title"})
    return sanitize_raw_payload(
        {key: value for key, value in data.items() if key not in blocked_keys}
    )


def _is_deleted_marker(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower() in DELETED_MARKERS


def _status_for_http_code(status_code: int) -> ConnectorStatus:
    if status_code in {401, 403}:
        return ConnectorStatus.PERMISSION_LIMITED
    if status_code == 429:
        return ConnectorStatus.RATE_LIMITED
    return ConnectorStatus.FAILED


def _safe_rate_headers(headers: Mapping[str, str]) -> dict[str, str]:
    safe_headers = {}
    for key in (
        "x-ratelimit-used",
        "x-ratelimit-remaining",
        "x-ratelimit-reset",
        "retry-after",
        "content-type",
    ):
        value = _header_value(headers, key)
        if value is not None:
            safe_headers[key] = value
    return safe_headers


def _header_value(headers: Mapping[str, str], name: str) -> str | None:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return None


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value: str | None) -> int | None:
    parsed = _parse_float(value)
    if parsed is None:
        return None
    return max(0, int(parsed))
