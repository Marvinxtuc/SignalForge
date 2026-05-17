#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.cookiejar
import re
import sys
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, urljoin, urlparse, urlunparse
from urllib.request import HTTPCookieProcessor, Request, build_opener


BODY_MARKERS = ("SignalForge", "Signals", "信号收件箱")
API_PATHS = (
    "/api/health",
    "/api/projects?page_size=1",
    "/api/settings/platforms",
)
USER_AGENT = "SignalForge-external-smoke/1.0"
SENSITIVE_QUERY_KEYS = {"sf_token"}
SENSITIVE_QUERY_RE = re.compile(r"(?i)(^|[?&;\s])((?:sf_token)=)(?:<redacted>|[^&;\s'\"<>)]*)")


class SmokeFailure(Exception):
    pass


@dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    body: str


def sanitize_url(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    query_parts = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        encoded_key = quote(key, safe="")
        encoded_value = "<redacted>" if key.lower() in SENSITIVE_QUERY_KEYS else quote(value, safe="")
        query_parts.append(f"{encoded_key}={encoded_value}")
    sanitized_query = "&".join(query_parts)
    return urlunparse(parsed._replace(query=sanitized_query))


def sanitize_text(text: str) -> str:
    return SENSITIVE_QUERY_RE.sub(r"\1\2<redacted>", text)


def emit(message: str) -> None:
    print(sanitize_text(message))


def fail(message: str) -> None:
    raise SmokeFailure(message)


def fetch(opener, url: str) -> FetchResult:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=20) as response:
            raw_body = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            body = raw_body.decode(charset, errors="replace")
            return FetchResult(url=url, status=response.getcode(), body=body)
    except HTTPError as exc:
        raw_body = exc.read()
        charset = exc.headers.get_content_charset() or "utf-8"
        body = raw_body.decode(charset, errors="replace")
        return FetchResult(url=url, status=exc.code, body=body)
    except URLError as exc:
        fail(f"request failed for {sanitize_url(url)}: {exc.reason}")
    except TimeoutError:
        fail(f"request timed out for {sanitize_url(url)}")

    fail(f"request failed for {sanitize_url(url)}")


def validate_no_server_error(result: FetchResult, label: str) -> None:
    if result.status == 500:
        fail(f"{label} returned HTTP 500: {sanitize_url(result.url)}")
    if "Internal Error" in result.body:
        fail(f"{label} body contains Internal Error: {sanitize_url(result.url)}")


def validate_reachable(result: FetchResult, label: str) -> None:
    if result.status < 200 or result.status >= 400:
        fail(f"{label} returned HTTP {result.status}: {sanitize_url(result.url)}")


def validate_page(result: FetchResult) -> None:
    validate_no_server_error(result, "page")
    validate_reachable(result, "page")
    if not any(marker in result.body for marker in BODY_MARKERS):
        markers = " / ".join(BODY_MARKERS)
        fail(f"page body missing required marker ({markers}): {sanitize_url(result.url)}")


def origin_for(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        fail("--url must be an absolute http(s) URL")
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))


def api_urls(origin: str) -> Iterable[str]:
    for path in API_PATHS:
        yield urljoin(origin, path)


def validate_api(opener, origin: str) -> None:
    for api_url in api_urls(origin):
        result = fetch(opener, api_url)
        label = f"api {urlparse(api_url).path}"
        validate_no_server_error(result, label)
        validate_reachable(result, label)
        emit(f"PASS: {label} returned HTTP {result.status}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run external SignalForge smoke validation.")
    parser.add_argument("--url", required=True, help="External SignalForge page URL to validate.")
    parser.add_argument(
        "--check-api",
        action="store_true",
        help="Also validate same-origin API smoke endpoints with the same CookieJar.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cookie_jar = http.cookiejar.CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))

    try:
        page_url = args.url
        origin = origin_for(page_url)
        page_result = fetch(opener, page_url)
        validate_page(page_result)

        if args.check_api:
            validate_api(opener, origin)

        emit(f"PASS: external smoke validation passed for {sanitize_url(page_url)}")
        return 0
    except SmokeFailure as exc:
        emit(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
