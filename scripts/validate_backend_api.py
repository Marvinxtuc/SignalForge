#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE_URL = os.environ.get("API_BASE_URL", "http://api:8000").rstrip("/")
COLLECTOR_NOT_AVAILABLE = "not_available_until_phase_3_or_later"


class ValidationFailure(Exception):
    pass


def _fail(message: str) -> None:
    raise ValidationFailure(message)


def _pass(message: str) -> None:
    print(f"PASS: {message}")


def _request(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    url = f"{API_BASE_URL}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"

    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body: Any = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw
        return exc.code, body
    except URLError as exc:
        _fail(f"Unable to reach API at {API_BASE_URL}: {exc}")


def _assert_status(status: int, expected: int, context: str, body: Any) -> None:
    if status != expected:
        _fail(f"{context} returned HTTP {status}, expected {expected}: {body}")


def _assert_no_secrets(value: Any, context: str) -> None:
    text = json.dumps(value, default=str).lower()
    forbidden = ["encrypted_payload", "bearer ", "api_key", "secret_key", "token"]
    hits = [marker for marker in forbidden if marker in text]
    if hits:
        _fail(f"{context} leaks forbidden markers: {hits}")


def _find_demo_project() -> str:
    status, body = _request("GET", "/api/projects", query={"page_size": 100})
    _assert_status(status, 200, "GET /api/projects", body)
    for item in body.get("items", []):
        if item.get("name") == "Polymarket Opportunity Radar":
            _pass("demo project is visible through Projects API")
            return str(item["id"])
    _fail("Demo project Polymarket Opportunity Radar not found; run seed_demo_data.py first")


def validate_health() -> None:
    status, body = _request("GET", "/health")
    _assert_status(status, 200, "GET /health", body)
    if body.get("status") != "ok" or body.get("phase") != "phase-2-backend-api":
        _fail(f"Unexpected health payload: {body}")
    _pass("GET /health returns phase-2-backend-api")


def validate_projects_and_keywords() -> str:
    name = "Phase 2 Backend Validation Project"
    status, body = _request(
        "POST",
        "/api/projects",
        {
            "name": name,
            "description": "Created by validate_backend_api.py",
            "platforms_enabled": {"reddit": True, "product_hunt": True},
            "collection_frequency": "manual",
        },
    )
    _assert_status(status, 201, "POST /api/projects", body)
    project_id = str(body["id"])
    _pass("Projects API creates project")

    status, body = _request("GET", f"/api/projects/{project_id}")
    _assert_status(status, 200, "GET /api/projects/{project_id}", body)
    if body.get("name") != name:
        _fail(f"Project fetch returned wrong project: {body}")
    _pass("Projects API fetches project")

    status, body = _request(
        "POST",
        f"/api/projects/{project_id}/keywords",
        {"keyword": "phase2 validation", "keyword_type": "main"},
    )
    _assert_status(status, 201, "POST /api/projects/{project_id}/keywords", body)
    if body.get("language") != "all" or body.get("enabled") is not True:
        _fail(f"Keyword defaults are wrong: {body}")
    _pass("Keywords API creates keyword with defaults")

    status, body = _request("GET", f"/api/projects/{project_id}/keywords")
    _assert_status(status, 200, "GET /api/projects/{project_id}/keywords", body)
    if not body:
        _fail("Keywords API returned empty keyword list after create")
    _pass("Keywords API lists project keywords")
    return project_id


def validate_signals(demo_project_id: str) -> str:
    status, body = _request(
        "GET",
        f"/api/projects/{demo_project_id}/signals",
        query={"min_pain_level": 70, "page_size": 20},
    )
    _assert_status(status, 200, "GET high value signals", body)
    items = body.get("items", [])
    if body.get("total", 0) < 2 or len(items) < 2:
        _fail(f"Expected at least 2 high value demo signals: {body}")
    for item in items:
        if item.get("pain_level", 0) < 70:
            _fail(f"Signal below high value threshold returned: {item}")
        if not item.get("source_url"):
            _fail(f"Signal response lost source_url: {item}")
    _pass("Signals high-value filter works and preserves source_url")
    return str(items[0]["id"])


def validate_opportunities(demo_project_id: str, signal_id: str) -> None:
    status, body = _request("GET", f"/api/projects/{demo_project_id}/opportunities")
    _assert_status(status, 200, "GET project opportunities", body)
    if body.get("total", 0) < 1 or not body.get("items"):
        _fail(f"Expected demo opportunities: {body}")
    opportunity_id = str(body["items"][0]["id"])
    _pass("Opportunities API lists demo opportunities")

    status, body = _request("GET", f"/api/opportunities/{opportunity_id}")
    _assert_status(status, 200, "GET opportunity detail", body)
    if str(body.get("id")) != opportunity_id:
        _fail(f"Opportunity detail returned wrong id: {body}")
    _pass("Opportunities API fetches opportunity detail")

    status, body = _request("POST", f"/api/signals/{signal_id}/create-opportunity")
    _assert_status(status, 200, "POST create opportunity from signal", body)
    if body.get("evidence_count") != 1 or not body.get("title"):
        _fail(f"Signal-derived opportunity payload is invalid: {body}")
    _pass("Opportunities API creates opportunity from signal without external calls")


def validate_reports(demo_project_id: str) -> None:
    status, body = _request("POST", f"/api/projects/{demo_project_id}/reports/markdown", {})
    _assert_status(status, 200, "POST markdown report", body)
    content = body.get("content", "")
    if body.get("format") != "markdown" or "source_url: https://example.com/" not in content:
        _fail(f"Markdown report did not preserve source_url: {body}")
    _assert_no_secrets(body, "Markdown report")
    _pass("Markdown report export works and preserves source_url")

    status, body = _request("POST", f"/api/projects/{demo_project_id}/reports/csv", {})
    _assert_status(status, 200, "POST csv report", body)
    content = body.get("content", "")
    required_header = "signal_id,platform,signal_type,pain_level,summary_zh,source_url,created_at"
    if body.get("format") != "csv" or required_header not in content or "https://example.com/" not in content:
        _fail(f"CSV report did not preserve required fields/source_url: {body}")
    _assert_no_secrets(body, "CSV report")
    _pass("CSV report export works and preserves source_url")


def validate_settings() -> None:
    status, body = _request("GET", "/api/settings/platforms")
    _assert_status(status, 200, "GET settings platforms", body)
    platforms = {item.get("platform") for item in body.get("platforms", [])}
    if platforms != {"reddit", "product_hunt", "x", "discord"}:
        _fail(f"Settings platforms are incomplete: {body}")
    _assert_no_secrets(body, "Settings platforms")
    _pass("Settings platform status includes P0/P1/P2 platforms")

    status, body = _request("GET", "/api/settings/credentials/status")
    _assert_status(status, 200, "GET credential status", body)
    _assert_no_secrets(body, "Credential status")
    credentials = {item.get("platform") for item in body.get("credentials", [])}
    if credentials != {"reddit", "product_hunt", "x", "discord"}:
        _fail(f"Credential statuses are incomplete: {body}")
    _pass("Settings credential status does not leak encrypted_payload or token material")


def validate_collect(project_id: str) -> None:
    status, body = _request("POST", f"/api/projects/{project_id}/collect")
    _assert_status(status, 200, "POST collect", body)
    if body.get("status") != "pending":
        _fail(f"Collect did not create pending job: {body}")
    if body.get("collector_execution") != COLLECTOR_NOT_AVAILABLE:
        _fail(f"Collect degradation marker missing: {body}")
    if body.get("log", {}).get("items_collected") != 0:
        _fail(f"Collect appears to have collected items: {body}")
    _pass("POST collect creates pending job without connector execution")


def main() -> int:
    try:
        validate_health()
        validation_project_id = validate_projects_and_keywords()
        demo_project_id = _find_demo_project()
        signal_id = validate_signals(demo_project_id)
        validate_opportunities(demo_project_id, signal_id)
        validate_reports(demo_project_id)
        validate_settings()
        validate_collect(validation_project_id)
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1

    print("PASS: backend API validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
