#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "web"
APP_ROOT = WEB_ROOT / "app"
API_CLIENT = WEB_ROOT / "lib" / "api.ts"
CONSTANTS = WEB_ROOT / "lib" / "constants.ts"
QUERY_HELPER = WEB_ROOT / "lib" / "query.ts"
API_ROUTE_PROXY = APP_ROOT / "api" / "[...path]" / "route.ts"
SIGNAL_FILTERS = WEB_ROOT / "components" / "signals" / "SignalFilters.tsx"

REQUIRED_ROUTES = ("/", "/signals", "/dashboard", "/opportunities", "/logs", "/settings", "/reports")
HTTP_SMOKE_ROUTES = REQUIRED_ROUTES
SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".json"}
IGNORED_DIRS = {"node_modules", ".next", "out", "dist", "coverage"}

FORBIDDEN_REAL_EXECUTION_OPTIONS = (
    "reddit_real",
    "product_hunt_real",
    "p0_real",
    "real_llm",
    "real_embedding",
    "x_real",
    "discord_real",
)

FORBIDDEN_ENDPOINT_MARKERS = (
    "oauth.reddit.com",
    "www.reddit.com/api",
    "api.producthunt.com",
    "api.openai.com",
    "api.anthropic.com",
    "api.x.com",
    "api.twitter.com",
    "discord.com/api",
    "/api/platform-credentials",
    "/api/credentials",
    "/api/admin/secrets",
)

TOKEN_LIKE_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~-]{20,}", re.IGNORECASE),
    re.compile(
        r"(?i)(api[_-]?key|token|secret|client[_-]?secret)\s*[:=]\s*['\"][A-Za-z0-9._~+/=-]{12,}['\"]"
    ),
)


class ValidationFailure(Exception):
    pass


def _fail(message: str) -> None:
    raise ValidationFailure(message)


def _pass(message: str) -> None:
    print(f"PASS: {message}")


def _skip(message: str) -> None:
    print(f"SKIP: {message}")


def _source_files() -> list[Path]:
    files: list[Path] = []
    for path in WEB_ROOT.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            files.append(path)
    return sorted(files)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _visible_route_for_page(page_file: Path) -> tuple[str, ...] | None:
    if page_file.name != "page.tsx":
        return None

    relative_parts = page_file.relative_to(APP_ROOT).parts[:-1]
    visible_parts = tuple(
        part
        for part in relative_parts
        if not (part.startswith("(") and part.endswith(")"))
        and not part.startswith("@")
        and not part.startswith("_")
    )
    return visible_parts


def validate_required_pages() -> None:
    if not APP_ROOT.is_dir():
        _fail("apps/web/app is missing")

    discovered = {
        _visible_route_for_page(path)
        for path in APP_ROOT.rglob("page.tsx")
        if _visible_route_for_page(path) is not None
    }

    missing: list[str] = []
    for route in REQUIRED_ROUTES:
        expected = tuple(part for part in route.strip("/").split("/") if part)
        if expected not in discovered:
            missing.append(route)

    if missing:
        _fail(f"required frontend pages are missing: {', '.join(missing)}")
    _pass("required Phase 6 pages exist")


def validate_ui_markers(files: list[Path]) -> None:
    text_by_file = {path: _read(path) for path in files}
    all_text = "\n".join(text_by_file.values())

    if "Open Source" not in all_text and "打开来源" not in all_text:
        _fail('Open Source / 打开来源 text is missing from frontend source')
    _pass("Open Source / 打开来源 text is present")

    if not re.search(r"\bhigh[-_\s]?value\b", all_text, re.IGNORECASE) and "高价值" not in all_text:
        _fail("high value / 高价值 marker is missing from frontend source")
    _pass("high value / 高价值 marker is present")

    settings_pages = [
        path
        for path in APP_ROOT.rglob("page.tsx")
        if _visible_route_for_page(path) == ("settings",)
    ]
    if not settings_pages:
        _fail("settings page is missing; cannot verify credential redaction")

    leaked_settings = [
        str(path.relative_to(ROOT))
        for path in settings_pages
        if "encrypted_payload" in _read(path)
    ]
    if leaked_settings:
        _fail(f"settings page renders encrypted_payload marker: {', '.join(leaked_settings)}")
    _pass("settings page does not render encrypted_payload")

    reports_pages = [
        path
        for path in APP_ROOT.rglob("page.tsx")
        if _visible_route_for_page(path) == ("reports",)
    ]
    if not reports_pages:
        _fail("reports page is missing; cannot verify export controls")

    reports_text = "\n".join(text_by_file.values()).lower()
    missing_exports = [marker for marker in ("markdown", "csv") if marker not in reports_text]
    if missing_exports:
        _fail(f"reports page is missing export markers: {', '.join(missing_exports)}")
    _pass("reports page exposes markdown and csv export controls")


def validate_api_client_boundary(files: list[Path]) -> None:
    if not API_CLIENT.is_file():
        _fail("apps/web/lib/api.ts is missing")
    if not CONSTANTS.is_file():
        _fail("apps/web/lib/constants.ts is missing")
    if not API_ROUTE_PROXY.is_file():
        _fail("apps/web/app/api/[...path]/route.ts is missing")

    api_text = _read(API_CLIENT)
    constants_text = _read(CONSTANTS)
    proxy_text = _read(API_ROUTE_PROXY)

    if "SERVER_API_BASE_URL" not in api_text or "PUBLIC_API_BASE_URL" not in api_text or "new URL(" not in api_text:
        _fail("API client does not centralize backend URL construction")
    if "invalid_backend_path" not in api_text or "https?:\\/\\/" not in api_text:
        _fail("API client does not reject absolute request paths")
    if "DEFAULT_SERVER_API_BASE_URL" not in constants_text or "http://api:8000" not in constants_text:
        _fail("SignalForge server backend default URL is missing")
    if "api.health" not in api_text and "health:" not in api_text:
        _fail("API client is missing health helper")
    if "/api/health" not in api_text or "/health" not in proxy_text:
        _fail("/api/health proxy mapping is missing")
    if "/api/${path}" not in proxy_text and "`/api/${path}`" not in proxy_text:
        _fail("route proxy does not map non-health paths to backend /api/*")
    for marker in ("cookie", "authorization", "sf_token"):
        if marker not in proxy_text:
            _fail(f"route proxy does not block forwarding {marker}")
    if "NODE_ENV" not in api_text or "production" not in api_text or "localhost" not in api_text or "invalid_public_api_base" not in api_text:
        _fail("API client is missing production localhost public API base guard")

    direct_fetch_files = []
    for path in files:
        text = _read(path)
        if "fetch(" in text and path not in {API_CLIENT, API_ROUTE_PROXY}:
            direct_fetch_files.append(str(path.relative_to(ROOT)))
        if re.search(r"\baxios\b", text):
            direct_fetch_files.append(str(path.relative_to(ROOT)))
    if direct_fetch_files:
        _fail(f"frontend source bypasses central API client: {', '.join(sorted(set(direct_fetch_files)))}")

    for path in files:
        text = _read(path)
        for marker in FORBIDDEN_ENDPOINT_MARKERS:
            if marker in text:
                _fail(f"forbidden endpoint marker {marker!r} found in {path.relative_to(ROOT)}")

    _pass("API client is limited to the SignalForge backend boundary")


def validate_query_helper_usage() -> None:
    if not QUERY_HELPER.is_file():
        _fail("apps/web/lib/query.ts is missing")

    query_text = _read(QUERY_HELPER)
    if "projectId" not in query_text or "sf_token" not in query_text:
        _fail("query helper does not preserve projectId and sf_token")
    if re.search(r"ALLOWED_QUERY_KEYS\s*=.*\.\.\.", query_text, re.DOTALL):
        _fail("query helper allowed keys are not explicit")

    required_users = (
        WEB_ROOT / "components" / "layout" / "Navigation.tsx",
        WEB_ROOT / "components" / "layout" / "ProjectSelector.tsx",
        WEB_ROOT / "components" / "opportunities" / "OpportunityCard.tsx",
        WEB_ROOT / "components" / "opportunities" / "OpportunityDetail.tsx",
    )
    missing = [
        str(path.relative_to(ROOT))
        for path in required_users
        if "buildAllowedQueryHref" not in _read(path)
    ]
    if missing:
        _fail(f"query helper is not used by required frontend components: {', '.join(missing)}")

    _pass("query token helper only preserves approved query values")


def validate_signal_platform_filter() -> None:
    if not SIGNAL_FILTERS.is_file():
        _fail("SignalFilters.tsx is missing")

    text = _read(SIGNAL_FILTERS)
    platform_section = re.search(r"<span[^>]*>\s*平台\s*</span>(.*?)</label>", text, re.DOTALL)
    if not platform_section or "<select" not in platform_section.group(1):
        _fail("SignalFilters platform control must be a select")

    for value in ("reddit", "product_hunt", "x", "discord"):
        if f'value="{value}"' not in platform_section.group(1):
            _fail(f"SignalFilters platform select is missing {value!r}")
    if "Product Hunt" not in platform_section.group(1):
        _fail("SignalFilters Product Hunt label is missing")

    _pass("SignalFilters platform select exposes approved values")


def validate_forbidden_values(files: list[Path]) -> None:
    for path in files:
        text = _read(path)
        for option in FORBIDDEN_REAL_EXECUTION_OPTIONS:
            if re.search(rf"['\"]{re.escape(option)}['\"]|\b{re.escape(option)}\b", text):
                _fail(f"forbidden real execution option {option!r} found in {path.relative_to(ROOT)}")

        for pattern in TOKEN_LIKE_PATTERNS:
            match = pattern.search(text)
            if match:
                _fail(f"token-like value found in {path.relative_to(ROOT)}: {match.group(0)[:16]}...")

    _pass("no forbidden execution options or token-like values found in frontend source")


def _http_get_status(url: str) -> int:
    request = Request(url, headers={"User-Agent": "SignalForge-frontend-validator/1.0"})
    with urlopen(request, timeout=5) as response:
        response.read()
        return response.status


def validate_optional_http_smoke(base_url: str, require_http: bool) -> None:
    base_url = base_url.rstrip("/")
    try:
        _http_get_status(f"{base_url}/")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        if require_http:
            _fail(f"frontend HTTP smoke required but {base_url} is not reachable: {exc}")
        _skip(f"frontend HTTP smoke skipped because {base_url} is not reachable")
        return

    failures: list[str] = []
    for route in HTTP_SMOKE_ROUTES:
        try:
            status = _http_get_status(f"{base_url}{route}")
        except HTTPError as exc:
            status = exc.code
        except (URLError, TimeoutError, OSError) as exc:
            failures.append(f"{route}: {exc}")
            continue

        if status != 200:
            failures.append(f"{route}: HTTP {status}")

    if failures:
        _fail(f"frontend HTTP smoke failed: {', '.join(failures)}")
    _pass("optional frontend HTTP smoke passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 6 Frontend MVP gates.")
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--require-http", action="store_true")
    args = parser.parse_args()

    try:
        files = _source_files()
        if not files:
            _fail("no frontend source files found")

        validate_required_pages()
        validate_ui_markers(files)
        validate_api_client_boundary(files)
        validate_query_helper_usage()
        validate_signal_platform_filter()
        validate_forbidden_values(files)
        validate_optional_http_smoke(args.base_url, args.require_http)
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1

    print("PASS: frontend MVP validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
