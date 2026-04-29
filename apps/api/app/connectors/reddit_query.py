from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import quote


API_BASE_URL = "https://oauth.reddit.com"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
MAX_REDDIT_LIMIT = 100


def build_api_url(endpoint: str, *, base_url: str = API_BASE_URL) -> str:
    normalized_base = base_url.rstrip("/")
    normalized_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    return f"{normalized_base}{normalized_endpoint}"


def build_keyword_search_query(
    keywords: Sequence[str],
    *,
    exclude_keywords: Sequence[str] = (),
) -> str:
    include_terms = [_quote_search_term(keyword) for keyword in keywords if keyword.strip()]
    exclude_terms = [f"-{_quote_search_term(keyword)}" for keyword in exclude_keywords if keyword.strip()]
    return " OR ".join(include_terms) + (
        f" {' '.join(exclude_terms)}" if include_terms and exclude_terms else " ".join(exclude_terms)
    )


def keyword_search_endpoint() -> str:
    return "/search"


def build_keyword_search_params(
    keywords: Sequence[str],
    *,
    exclude_keywords: Sequence[str] = (),
    limit: int = 25,
    sort: str = "new",
    time_filter: str = "week",
    after: str | None = None,
) -> dict[str, str | int]:
    params: dict[str, str | int] = {
        "q": build_keyword_search_query(keywords, exclude_keywords=exclude_keywords),
        "limit": _clamp_limit(limit),
        "sort": sort,
        "t": time_filter,
        "raw_json": 1,
    }
    if after:
        params["after"] = after
    return params


def build_keyword_search_url(*, base_url: str = API_BASE_URL) -> str:
    return build_api_url(keyword_search_endpoint(), base_url=base_url)


def build_subreddit_watch_endpoint(subreddit: str, *, sort: str = "new") -> str:
    normalized_subreddit = normalize_subreddit(subreddit)
    return f"/r/{quote(normalized_subreddit, safe='')}/{sort}"


def build_subreddit_watch_params(
    *,
    limit: int = 25,
    after: str | None = None,
) -> dict[str, str | int]:
    params: dict[str, str | int] = {
        "limit": _clamp_limit(limit),
        "raw_json": 1,
    }
    if after:
        params["after"] = after
    return params


def build_subreddit_watch_url(
    subreddit: str,
    *,
    sort: str = "new",
    base_url: str = API_BASE_URL,
) -> str:
    return build_api_url(build_subreddit_watch_endpoint(subreddit, sort=sort), base_url=base_url)


def build_comments_endpoint(subreddit: str, post_id: str) -> str:
    normalized_subreddit = normalize_subreddit(subreddit)
    normalized_post_id = post_id.strip()
    if not normalized_post_id:
        raise ValueError("post_id must be non-empty")
    return f"/r/{quote(normalized_subreddit, safe='')}/comments/{quote(normalized_post_id, safe='')}"


def build_comments_params(
    *,
    limit: int = 10,
    sort: str = "top",
    depth: int = 1,
) -> dict[str, str | int]:
    return {
        "limit": _clamp_limit(limit),
        "sort": sort,
        "depth": max(0, depth),
        "raw_json": 1,
    }


def build_comments_url(
    subreddit: str,
    post_id: str,
    *,
    base_url: str = API_BASE_URL,
) -> str:
    return build_api_url(build_comments_endpoint(subreddit, post_id), base_url=base_url)


def normalize_subreddit(subreddit: str) -> str:
    normalized = subreddit.strip()
    if normalized.startswith("/"):
        normalized = normalized.lstrip("/")
    if normalized.lower().startswith("r/"):
        normalized = normalized[2:]
    normalized = normalized.strip("/")
    if not normalized:
        raise ValueError("subreddit must be non-empty")
    return normalized


def _quote_search_term(value: str) -> str:
    term = value.strip()
    if not term:
        return ""
    if any(character.isspace() for character in term):
        escaped = term.replace('"', r"\"")
        return f'"{escaped}"'
    return term


def _clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_REDDIT_LIMIT))
