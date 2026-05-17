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
    name = f"SignalForge API E2E Personal Workflow {datetime.now(UTC).isoformat()}"
    status, body = _request(
        "POST",
        "/api/projects",
        {
            "name": name,
            "description": "Created by scripts/validate_personal_workflow.py",
            "platforms_enabled": {"mock": True, "reddit": False, "product_hunt": False},
            "collection_frequency": "manual",
        },
    )
    _assert_status(status, 201, "POST /api/projects", body)
    _assert_no_forbidden_markers(body, "project create response")
    project_id = str(body["id"])
    _pass("test project created through API")
    return project_id


def _delete_project(project_id: str) -> None:
    if KEEP_PROJECT:
        print(f"INFO: kept validation project {project_id}")
        return
    status, body = _request("DELETE", f"/api/projects/{project_id}")
    if status not in {200, 404}:
        _fail(f"DELETE /api/projects/{project_id} returned HTTP {status}: {body}")
    _pass("test project cleanup completed")


def _create_keywords(project_id: str) -> None:
    keywords = [
        {"keyword": "wallet onboarding", "keyword_type": "main"},
        {"keyword": "pricing clarity", "keyword_type": "related"},
        {"keyword": "giveaway", "keyword_type": "exclude"},
    ]
    for payload in keywords:
        status, body = _request("POST", f"/api/projects/{project_id}/keywords", payload)
        _assert_status(status, 201, "POST project keyword", body)
        _assert_no_forbidden_markers(body, "keyword create response")

    status, body = _request("GET", f"/api/projects/{project_id}/keywords")
    _assert_status(status, 200, "GET project keywords", body)
    keyword_types = {item.get("keyword_type") for item in body}
    if not {"main", "exclude"}.issubset(keyword_types):
        _fail(f"include/exclude keywords are missing: {body}")
    _pass("include and exclude keywords created and listed")


def _collect_mock(project_id: str) -> None:
    status, body = _request("POST", f"/api/projects/{project_id}/collect", {"execution_mode": "mock"})
    _assert_status(status, 200, "POST mock collect", body)
    _assert_no_forbidden_markers(body, "mock collect response")
    if body.get("collector_execution") != "mock":
        _fail(f"mock collect mode marker missing: {body}")
    log = body.get("log") or {}
    if body.get("status") != "success" or log.get("status") != "success":
        _fail(f"mock collect did not succeed: {body}")
    if int(log.get("items_collected") or 0) < 5:
        _fail(f"mock collect did not collect expected raw_items: {body}")
    if int(log.get("items_inserted") or 0) < 1:
        _fail(
            "mock collect inserted no raw_items; remove stale mock validation projects "
            "or run against a clean local database"
        )
    _pass("mock collection inserted raw_items")


def _process(project_id: str, mode: str, reprocess: bool) -> dict[str, Any]:
    status, body = _request(
        "POST",
        f"/api/projects/{project_id}/process",
        {"mode": mode, "reprocess": reprocess},
    )
    _assert_status(status, 200, f"POST process mode={mode}", body)
    _assert_no_forbidden_markers(body, f"processing response mode={mode}")
    if body.get("mode") != mode:
        _fail(f"processing mode marker mismatch for {mode}: {body}")
    if int(body.get("total_raw_items") or 0) < 5:
        _fail(f"processing did not see mock raw_items: {body}")
    if int(body.get("total_signals") or 0) < 3:
        _fail(f"processing did not create signals: {body}")
    if mode == "fallback_only" and int(body.get("fallback_classification_count") or 0) < 1:
        _fail(f"fallback processing was not counted: {body}")
    _pass(f"{mode} processing completed with mode marker")
    return body


def _validate_signals(project_id: str) -> None:
    status, body = _request("GET", f"/api/projects/{project_id}/signals", query={"page_size": 20})
    _assert_status(status, 200, "GET project signals", body)
    _assert_no_forbidden_markers(body, "signals response")
    items = body.get("items", [])
    if len(items) < 3 or int(body.get("total") or 0) < 3:
        _fail(f"expected at least 3 processed signals: {body}")
    for item in items:
        if not item.get("source_url"):
            _fail(f"signal lost source_url: {item}")
        if not item.get("recommended_action"):
            _fail(f"signal lost recommended_action: {item}")

    high_status, high_body = _request(
        "GET",
        f"/api/projects/{project_id}/signals",
        query={"min_pain_level": 70, "page_size": 20},
    )
    _assert_status(high_status, 200, "GET high-value signal filter", high_body)
    for item in high_body.get("items", []):
        if int(item.get("pain_level") or 0) < 70:
            _fail(f"high-value filter returned low-pain signal: {item}")
    if int(high_body.get("total") or 0) < 1:
        _fail(f"mock E2E did not produce a high-value signal: {high_body}")
    _pass("signals preserve source_url/recommended_action and high-value filter is valid")


def _validate_opportunities(project_id: str) -> None:
    status, body = _request("GET", f"/api/projects/{project_id}/opportunities", query={"page_size": 20})
    _assert_status(status, 200, "GET project opportunities", body)
    _assert_no_forbidden_markers(body, "opportunities response")
    if int(body.get("total") or 0) < 1 or not body.get("items"):
        _fail(f"expected processing to create opportunities: {body}")
    for item in body["items"]:
        if not item.get("title") or int(item.get("evidence_count") or 0) < 1:
            _fail(f"opportunity is missing business value fields: {item}")
    _pass("opportunities created from processed signals")


def _validate_reports(project_id: str) -> None:
    request = {"min_pain_level": 0}
    status, body = _request("POST", f"/api/projects/{project_id}/reports/markdown", request)
    _assert_status(status, 200, "POST markdown report", body)
    _assert_no_forbidden_markers(body, "markdown report")
    content = body.get("content", "")
    if body.get("format") != "markdown" or "High Value Signals" not in content:
        _fail(f"markdown report returned wrong format/sections: {body}")
    if "source_url:" not in content or "recommended_action:" not in content:
        _fail(f"markdown report is missing source_url or recommended_action: {body}")

    status, body = _request("POST", f"/api/projects/{project_id}/reports/csv", request)
    _assert_status(status, 200, "POST csv report", body)
    _assert_no_forbidden_markers(body, "csv report")
    content = body.get("content", "")
    required_header = "signal_id,platform,signal_type,pain_level,summary_zh,recommended_action,source_url,mode,created_at"
    if body.get("format") != "csv" or required_header not in content:
        _fail(f"csv report returned wrong format/header: {body}")
    _pass("mock-project reports render and omit forbidden secret markers")


def _find_demo_project() -> str:
    status, body = _request("GET", "/api/projects", query={"page_size": 100})
    _assert_status(status, 200, "GET /api/projects", body)
    for item in body.get("items", []):
        if item.get("name") == DEMO_PROJECT_NAME:
            return str(item["id"])
    _fail(f"demo project {DEMO_PROJECT_NAME!r} not found; run scripts/seed_demo_data.py first")


def _validate_demo_report_source_url() -> None:
    project_id = _find_demo_project()
    status, body = _request(
        "GET",
        f"/api/projects/{project_id}/signals",
        query={"min_pain_level": 70, "page_size": 20},
    )
    _assert_status(status, 200, "GET demo high-value signals", body)
    high_value_urls = [item.get("source_url") for item in body.get("items", []) if item.get("source_url")]
    if not high_value_urls:
        _fail(f"demo project has no high-value source_url evidence: {body}")

    for report_type in ("markdown", "csv"):
        status, report = _request("POST", f"/api/projects/{project_id}/reports/{report_type}", {})
        _assert_status(status, 200, f"POST demo {report_type} report", report)
        _assert_no_forbidden_markers(report, f"demo {report_type} report")
        content = report.get("content", "")
        if high_value_urls[0] not in content:
            _fail(f"demo {report_type} report lost high-value source_url {high_value_urls[0]}: {report}")
    _pass("demo high-value reports preserve source_url and omit forbidden secret markers")


def validate() -> None:
    status, body = _request("GET", "/health")
    _assert_status(status, 200, "GET /health", body)
    _pass("API health endpoint is reachable")

    project_id: str | None = None
    try:
        project_id = _create_project()
        _create_keywords(project_id)
        _collect_mock(project_id)
        mock_summary = _process(project_id, "mock", False)
        if int(mock_summary.get("opportunity_count") or 0) < 1:
            _fail(f"mock processing did not produce opportunities: {mock_summary}")
        _validate_signals(project_id)
        _validate_opportunities(project_id)
        _validate_reports(project_id)
        _process(project_id, "fallback_only", True)
        _validate_demo_report_source_url()
    finally:
        if project_id:
            _delete_project(project_id)


def main() -> int:
    try:
        validate()
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: personal workflow API E2E validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
