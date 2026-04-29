#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "sop/mvp-lifecycle.yml",
    "sop/phase-gates.yml",
    "sop/acceptance-gates.yml",
    "docs/acceptance/acceptance-checklist.md",
    "docs/acceptance/final-acceptance-report.md",
    "docs/testing/test-report.md",
    "docs/release/v0.1.0-mvp-release-notes.md",
]

MUST_PASS = [
    "docker_compose_up",
    "api_health_ok",
    "web_accessible",
    "demo_seed_ok",
    "mock_collection_ok",
    "reddit_connector_degraded_or_success",
    "product_hunt_connector_degraded_or_success",
    "raw_items_to_signals_ok",
    "signals_to_clusters_ok",
    "clusters_to_opportunities_ok",
    "signal_inbox_visible",
    "high_value_signals_highlighted",
    "open_source_link_visible",
    "csv_export_ok",
    "markdown_export_ok",
    "no_token_leak",
    "docs_complete",
    "final_acceptance_report_present",
]

HARD_FAIL = [
    "token_in_logs",
    "token_in_frontend_response",
    "source_url_missing",
    "signal_inbox_missing",
    "llm_json_failure_crashes_job",
    "connector_failure_crashes_system",
    "no_rollback_doc",
    "no_test_report",
    "missing_signal_quality_gate",
    "missing_signal_to_opportunity_flow",
    "p0_scope_drift_to_x_or_discord",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require_text(path: str, markers: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            fail(f"{path} missing marker: {marker}")


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required acceptance assets: " + ", ".join(missing))

    gates = (ROOT / "sop/acceptance-gates.yml").read_text(encoding="utf-8")
    for item in MUST_PASS + HARD_FAIL:
        if item not in gates:
            fail(f"acceptance-gates.yml missing item: {item}")

    require_text("docs/acceptance/final-acceptance-report.md", ["Status: NOT_STARTED", "Phase: Phase -1 Governance Bootstrap"])
    require_text("docs/testing/test-report.md", ["Status: NOT_STARTED", "Phase: Phase -1 Governance Bootstrap"])
    require_text("docs/release/v0.1.0-mvp-release-notes.md", ["Status: NOT_STARTED", "Phase: Phase -1 Governance Bootstrap"])

    lifecycle = (ROOT / "sop/mvp-lifecycle.yml").read_text(encoding="utf-8")
    for marker in ["reddit", "product_hunt", "x", "discord", "High Value Signal Density"]:
        if marker not in lifecycle:
            fail(f"mvp-lifecycle.yml missing marker: {marker}")

    print("PASS: acceptance validation")


if __name__ == "__main__":
    main()
