#!/usr/bin/env python3
"""Validate SignalForge Phase 7 final acceptance documentation.

This script is intentionally documentation-focused. It should fail while the
Phase 7 release-freeze documents are still placeholders, and pass only after
the final acceptance, release, rollback, tag, and manual-action records are
explicitly finalized.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "final acceptance report": "docs/acceptance/final-acceptance-report.md",
    "acceptance checklist": "docs/acceptance/acceptance-checklist.md",
    "test report": "docs/testing/test-report.md",
    "coverage summary": "docs/testing/coverage-summary.md",
    "release notes": "docs/release/v0.1.0-mvp-release-notes.md",
    "rollback runbook": "docs/runbooks/rollback.md",
    "tag checklist": "docs/release/tag-checklist.md",
    "branch protection runbook": "docs/runbooks/git-branch-protection.md",
    "README": "README.md",
    "phase gates": "sop/phase-gates.yml",
    "acceptance gates": "sop/acceptance-gates.yml",
}

PHASE_PASS_MARKERS = [
    "Phase -1 Governance Bootstrap: PASS",
    "Phase 0 Infrastructure: PASS",
    "Phase 1 Data Model: PASS",
    "Phase 2 Backend API: PASS",
    "Phase 3 Connector Abstraction: PASS",
    "Phase 4 P0 Connectors: PASS",
    "Phase 5 Processing Pipeline: PASS",
    "Phase 6 Frontend MVP: PASS",
]

FINAL_REPORT_MARKERS = [
    "MVP local/mock acceptance: PASS",
    "Release readiness: PASS_WITH_MANUAL_ACTIONS",
    "Real Reddit smoke: NOT_EXECUTED / pending token",
    "Real Product Hunt smoke: NOT_EXECUTED / pending token",
    "Real LLM smoke: NOT_EXECUTED / pending token",
    "Real embedding smoke: NOT_EXECUTED / pending token",
    "Phase 7 Testing / Acceptance / Release Freeze",
]

TAG_MARKERS = [
    "tag_status: pending_manual_owner_action",
    "target_tag: v0.1.0-mvp",
    "accepted_commit:",
    "reason: tag creation requires explicit owner approval",
    "push_status: not_pushed",
]

RELEASE_NOTE_MARKERS = [
    "v0.1.0-mvp",
    "Included",
    "Not Included",
    "Reddit",
    "Product Hunt",
    "Processing Pipeline",
    "Signal Inbox",
    "Opportunity Board",
    "Production deployment",
    "Auth",
    "X",
    "Discord",
]

BACKLOG_MARKERS = [
    "@owner",
    "branch protection",
    "Real Reddit smoke",
    "Real Product Hunt smoke",
    "Real LLM smoke",
    "Real embedding smoke",
    "X Connector",
    "Discord Connector",
    "auth",
    "production deployment",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: str) -> str:
    file_path = ROOT / path
    if not file_path.is_file():
        fail(f"missing required file: {path}")
    return file_path.read_text(encoding="utf-8")


def require_markers(label: str, text: str, markers: list[str]) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        fail(f"{label} missing marker(s): " + ", ".join(missing))


def require_markers_case_insensitive(label: str, text: str, markers: list[str]) -> None:
    lower = text.lower()
    missing = [marker for marker in markers if marker.lower() not in lower]
    if missing:
        fail(f"{label} missing marker(s): " + ", ".join(missing))


def forbid_markers(label: str, text: str, markers: list[str]) -> None:
    hits = [marker for marker in markers if marker in text]
    if hits:
        fail(f"{label} contains forbidden marker(s): " + ", ".join(hits))


def main() -> None:
    missing = [
        f"{label} ({path})"
        for label, path in REQUIRED_FILES.items()
        if not (ROOT / path).is_file()
    ]
    if missing:
        fail("missing required final acceptance asset(s): " + ", ".join(missing))

    final_report = read(REQUIRED_FILES["final acceptance report"])
    checklist = read(REQUIRED_FILES["acceptance checklist"])
    test_report = read(REQUIRED_FILES["test report"])
    coverage_summary = read(REQUIRED_FILES["coverage summary"])
    release_notes = read(REQUIRED_FILES["release notes"])
    rollback = read(REQUIRED_FILES["rollback runbook"])
    tag_checklist = read(REQUIRED_FILES["tag checklist"])
    branch_protection = read(REQUIRED_FILES["branch protection runbook"])
    readme = read(REQUIRED_FILES["README"])
    phase_gates = read(REQUIRED_FILES["phase gates"])
    acceptance_gates = read(REQUIRED_FILES["acceptance gates"])

    require_markers("final acceptance report", final_report, PHASE_PASS_MARKERS)
    require_markers("final acceptance report", final_report, FINAL_REPORT_MARKERS)
    require_markers("tag checklist", tag_checklist, TAG_MARKERS)
    require_markers_case_insensitive("release notes", release_notes, RELEASE_NOTE_MARKERS)
    require_markers("rollback runbook", rollback, ["git revert", "v0.1.0-mvp", "git tag -d"])
    require_markers(
        "branch protection runbook",
        branch_protection,
        ["@owner", "branch protection", "manual"],
    )

    combined = "\n".join(
        [
            final_report,
            checklist,
            test_report,
            coverage_summary,
            release_notes,
            rollback,
            tag_checklist,
            readme,
            phase_gates,
            acceptance_gates,
        ]
    )
    require_markers("final acceptance asset set", combined, BACKLOG_MARKERS)
    require_markers(
        "final acceptance asset set",
        combined,
        [
            "PASS_WITH_MANUAL_ACTIONS",
            "NOT_EXECUTED / pending token",
            "pending_manual_owner_action",
        ],
    )
    forbid_markers(
        "final acceptance report",
        final_report,
        [
            "Real Reddit smoke: PASS",
            "Real Product Hunt smoke: PASS",
            "Real LLM smoke: PASS",
            "Real embedding smoke: PASS",
            "tag_status: created",
            "Final MVP acceptance has not started",
            "Phase 7 final acceptance skeleton",
        ],
    )

    print("PASS: final acceptance validation")


if __name__ == "__main__":
    main()
