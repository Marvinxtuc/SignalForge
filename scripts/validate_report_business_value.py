#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
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


def _find_demo_project() -> str:
    status, body = _request("GET", "/api/projects", query={"page_size": 100})
    _assert_status(status, 200, "GET /api/projects", body)
    for item in body.get("items", []):
        if item.get("name") == DEMO_PROJECT_NAME:
            _assert_no_forbidden_markers(item, "demo project payload")
            _pass("demo project is available through API")
            return str(item["id"])
    _fail(f"demo project {DEMO_PROJECT_NAME!r} not found; run scripts/seed_demo_data.py first")


def _validate_high_value_signals(project_id: str) -> list[dict[str, Any]]:
    status, body = _request(
        "GET",
        f"/api/projects/{project_id}/signals",
        query={"min_pain_level": 70, "page_size": 20},
    )
    _assert_status(status, 200, "GET high-value signals", body)
    _assert_no_forbidden_markers(body, "high-value signals response")
    items = body.get("items", [])
    if int(body.get("total") or 0) < 2 or len(items) < 2:
        _fail(f"expected at least 2 high-value demo signals: {body}")
    for item in items:
        if int(item.get("pain_level") or 0) < 70:
            _fail(f"high-value signal below threshold: {item}")
        if not item.get("source_url"):
            _fail(f"high-value signal lost source_url: {item}")
        if not item.get("recommended_action"):
            _fail(f"high-value signal lost recommended_action: {item}")
    _pass("high-value signals preserve source_url and recommended_action")
    return items


def _validate_opportunities(project_id: str) -> None:
    status, body = _request("GET", f"/api/projects/{project_id}/opportunities", query={"page_size": 20})
    _assert_status(status, 200, "GET opportunities", body)
    _assert_no_forbidden_markers(body, "opportunities response")
    items = body.get("items", [])
    if int(body.get("total") or 0) < 1 or not items:
        _fail(f"expected at least one opportunity: {body}")
    for item in items:
        if not item.get("title"):
            _fail(f"opportunity is missing title: {item}")
        if int(item.get("evidence_count") or 0) < 1:
            _fail(f"opportunity is missing evidence_count: {item}")
        if item.get("opportunity_score") is None:
            _fail(f"opportunity is missing opportunity_score: {item}")
    _pass("opportunities expose business value fields")


def _validate_reports(project_id: str, high_value_signals: list[dict[str, Any]]) -> None:
    expected_urls = {item["source_url"] for item in high_value_signals[:2]}

    status, body = _request("POST", f"/api/projects/{project_id}/reports/markdown", {})
    _assert_status(status, 200, "POST markdown report", body)
    _assert_no_forbidden_markers(body, "markdown report")
    markdown = body.get("content", "")
    if body.get("format") != "markdown":
        _fail(f"markdown report returned wrong format: {body}")
    missing_urls = [url for url in expected_urls if url not in markdown]
    if missing_urls:
        _fail(f"markdown report lost high-value source_url(s): {missing_urls}")
    if "High Value Signals" not in markdown or "Opportunities" not in markdown:
        _fail(f"markdown report lost business value sections: {body}")
    if "recommended_action:" not in markdown:
        _fail(f"markdown report is missing recommended action content: {body}")

    status, body = _request("POST", f"/api/projects/{project_id}/reports/csv", {})
    _assert_status(status, 200, "POST csv report", body)
    _assert_no_forbidden_markers(body, "csv report")
    csv_content = body.get("content", "")
    required_header = "signal_id,platform,signal_type,pain_level,summary_zh,recommended_action,source_url,mode,created_at"
    if body.get("format") != "csv" or required_header not in csv_content:
        _fail(f"csv report returned wrong format/header: {body}")
    missing_urls = [url for url in expected_urls if url not in csv_content]
    if missing_urls:
        _fail(f"csv report lost high-value source_url(s): {missing_urls}")
    _pass("business reports preserve high-value evidence and omit forbidden secret markers")


def validate() -> None:
    status, body = _request("GET", "/health")
    _assert_status(status, 200, "GET /health", body)
    _pass("API health endpoint is reachable")

    project_id = _find_demo_project()
    high_value_signals = _validate_high_value_signals(project_id)
    _validate_opportunities(project_id)
    _validate_reports(project_id, high_value_signals)


def main() -> int:
    try:
        validate()
    except ValidationFailure as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: report business value API validation succeeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
