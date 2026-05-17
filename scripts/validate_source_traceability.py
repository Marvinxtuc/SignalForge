#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
KEEP_PROJECT = os.environ.get("SIGNALFORGE_KEEP_E2E_PROJECT") == "1"
DEMO_PROJECT_NAME = os.environ.get("SIGNALFORGE_DEMO_PROJECT_NAME", "Polymarket Opportunity Radar")
FORBIDDEN_REPORT_MARKERS = (
    "sf_token",
    "product_hunt_token",
    "reddit_client_secret",
    "openai_api_key",
    "encrypted_payload",
)


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

    try:
        with urlopen(Request(url, data=data, headers=headers, method=method), timeout=20) as response:
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
        _fail(f"unable to reach API at {API_BASE_URL}: {exc}")


def _assert_status(status: int, expected: int, context: str, body: Any) -> None:
    if status != expected:
        _fail(f"{context} returned HTTP {status}, expected {expected}: {body}")


def _assert_no_forbidden_markers(value: Any, context: str) -> None:
    text = json.dumps(value, default=str).lower()
    hits = [marker for marker in FORBIDDEN_REPORT_MARKERS if marker in text]
    if hits:
        _fail(f"{context} contains forbidden marker(s): {hits}")


def _create_project() -> str:
    status, body = _request(
        "POST",
        "/api/projects",
        {
            "name": f"SignalForge API E2E Traceability {datetime.now(UTC).isoformat()}",
            "description": "Created by scripts/validate_source_traceability.py",
            "platforms_enabled": {"mock": True},
            "collection_frequency": "manual",
        },
    )
    _assert_status(status, 201, "POST /api/projects", body)
    _assert_no_forbidden_markers(body, "project create response")
    _pass("traceability test project created")
    return str(body["id"])


def _delete_project(project_id: str) -> None:
    if KEEP_PROJECT:
        print(f"INFO: kept validation project {project_id}")
        return
    status, body = _request("DELETE", f"/api/projects/{project_id}")
    if status not in {200, 404}:
        _fail(f"DELETE /api/projects/{project_id} returned HTTP {status}: {body}")
    _pass("traceability test project cleanup completed")


def _prepare_project(project_id: str) -> None:
    for payload in (
        {"keyword": "wallet onboarding", "keyword_type": "main"},
        {"keyword": "pricing clarity", "keyword_type": "related"},
        {"keyword": "giveaway", "keyword_type": "exclude"},
    ):
        status, body = _request("POST", f"/api/projects/{project_id}/keywords", payload)
        _assert_status(status, 201, "POST keyword", body)
        _assert_no_forbidden_markers(body, "keyword response")
    _pass("traceability include/exclude keywords created")

    status, body = _request("POST", f"/api/projects/{project_id}/collect", {"execution_mode": "mock"})
    _assert_status(status, 200, "POST mock collect", body)
    _assert_no_forbidden_markers(body, "mock collect response")
    if body.get("collector_execution") != "mock":
        _fail(f"collector mode marker missing: {body}")
    log = body.get("log") or {}
    if int(log.get("items_inserted") or 0) < 5:
        _fail(
            "mock collect inserted no raw_items; remove stale mock validation projects "
            "or run against a clean local database"
        )
    _pass("mock raw_items collected with mode marker")


def _process_project(project_id: str) -> None:
    for mode, reprocess in (("mock", False), ("fallback_only", True)):
        status, body = _request(
            "POST",
            f"/api/projects/{project_id}/process",
            {"mode": mode, "reprocess": reprocess},
        )
        _assert_status(status, 200, f"POST process mode={mode}", body)
        _assert_no_forbidden_markers(body, f"processing response mode={mode}")
        if body.get("mode") != mode:
            _fail(f"processing mode marker mismatch: {body}")
        if int(body.get("total_raw_items") or 0) < 5 or int(body.get("total_signals") or 0) < 3:
            _fail(f"processing lost raw_items/signals: {body}")
    _pass("mock and fallback processing preserve mode markers")


def _validate_signal_trace(project_id: str) -> list[str]:
    status, body = _request("GET", f"/api/projects/{project_id}/signals", query={"page_size": 20})
    _assert_status(status, 200, "GET signals", body)
    _assert_no_forbidden_markers(body, "signals response")
    items = body.get("items", [])
    if len(items) < 3:
        _fail(f"expected at least 3 signals for source traceability: {body}")

    source_urls: list[str] = []
    for item in items:
        source_url = item.get("source_url")
        if not source_url:
            _fail(f"signal list item lost source_url: {item}")
        if not item.get("recommended_action"):
            _fail(f"signal list item lost recommended_action: {item}")
        source_urls.append(source_url)

        status, detail = _request("GET", f"/api/signals/{item['id']}")
        _assert_status(status, 200, "GET signal detail", detail)
        _assert_no_forbidden_markers(detail, "signal detail response")
        if detail.get("source_url") != source_url:
            _fail(f"signal detail source_url mismatch: list={item} detail={detail}")
        if detail.get("recommended_action") != item.get("recommended_action"):
            _fail(f"signal detail recommended_action mismatch: list={item} detail={detail}")

    _pass("signal list/detail preserve source_url and recommended_action")
    return source_urls


def _find_demo_project() -> str:
    status, body = _request("GET", "/api/projects", query={"page_size": 100})
    _assert_status(status, 200, "GET /api/projects", body)
    for item in body.get("items", []):
        if item.get("name") == DEMO_PROJECT_NAME:
            return str(item["id"])
    _fail(f"demo project {DEMO_PROJECT_NAME!r} not found; run scripts/seed_demo_data.py first")


def _validate_report_trace() -> None:
    project_id = _find_demo_project()
    status, body = _request(
        "GET",
        f"/api/projects/{project_id}/signals",
        query={"min_pain_level": 70, "page_size": 20},
    )
    _assert_status(status, 200, "GET demo high-value signals", body)
    expected_urls = {item["source_url"] for item in body.get("items", [])[:2] if item.get("source_url")}
    if not expected_urls:
        _fail(f"demo project has no high-value source_url evidence: {body}")

    for report_type in ("markdown", "csv"):
        status, body = _request(
            "POST",
            f"/api/projects/{project_id}/reports/{report_type}",
            {},
        )
        _assert_status(status, 200, f"POST {report_type} report", body)
        _assert_no_forbidden_markers(body, f"{report_type} report")
        content = body.get("content", "")
        missing = [url for url in expected_urls if url not in content]
        if missing:
            _fail(f"{report_type} report lost source_url(s): {missing}")
    _pass("demo markdown/csv reports preserve source_url and omit forbidden secret markers")


def validate() -> None:
    status, body = _request("GET", "/health")
    _assert_status(status, 200, "GET /health", body)
    _pass("API health endpoint is reachable")

    project_id: str | None = None
    try:
        project_id = _create_project()
        _prepare_project(project_id)
        _process_project(project_id)
        _validate_signal_trace(project_id)
        _validate_report_trace()
    finally:
        if project_id:
            _delete_project(project_id)


def main() -> int:
    try:
        validate()
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: source traceability API validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
