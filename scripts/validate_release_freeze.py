#!/usr/bin/env python3
"""Validate SignalForge Phase 7 release-freeze readiness.

Modes:
- pre-commit: allow expected Phase 7 docs/scripts/CI changes, but reject app,
  infra, migration, root feature-path, and .env drift.
- final: require a clean worktree after the Phase 7 commit.
- ci: skip local branch and clean-worktree requirements for GitHub Actions.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TARGET_BRANCH = "feature/mvp-p0"

REQUIRED_COMMITS = {
    "83c9537": "feat: add phase 6 frontend mvp",
    "2b76e5f": "feat: add phase 5 processing pipeline",
    "09c4fd2": "feat: add phase 4 p0 connectors",
    "27b610c": "feat: add phase 3 connector abstraction",
    "df9726b": "feat: add phase 2 backend api",
    "422f1ed": "feat: add phase 1 data model and migrations",
}

REQUIRED_RELEASE_FILES = [
    "docs/acceptance/final-acceptance-report.md",
    "docs/acceptance/acceptance-checklist.md",
    "docs/testing/test-report.md",
    "docs/testing/coverage-summary.md",
    "docs/release/v0.1.0-mvp-release-notes.md",
    "docs/release/tag-checklist.md",
    "docs/runbooks/rollback.md",
    "docs/runbooks/git-branch-protection.md",
    "README.md",
    "sop/phase-gates.yml",
    "sop/acceptance-gates.yml",
]

ALLOWED_PRECOMMIT_PATHS = {
    "README.md",
    ".github/pull_request_template.md",
    ".github/workflows/ci-acceptance.yml",
    "scripts/validate_final_acceptance.py",
    "scripts/validate_release_freeze.py",
    "apps/web/components/opportunities/opportunityView.ts",
}

ALLOWED_PRECOMMIT_PREFIXES = (
    "docs/",
    "sop/",
)

FORBIDDEN_PRECOMMIT_PREFIXES = (
    "apps/api/app/",
    "apps/web/",
    "infra/",
)

FORBIDDEN_ROOT_PATHS = [
    "connectors",
    "pipeline",
    "frontend",
    "backend",
]

MIGRATION_MARKERS = (
    "/migrations/versions/",
    "apps/api/migrations/versions/",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def run_git(args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def run_git_raw(args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def parse_status_line(line: str) -> str:
    # Porcelain v1 is two status chars, a space, then path. Renames contain
    # "old -> new"; use the destination path for boundary checks.
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip()


def git_status_paths() -> list[str]:
    output = run_git_raw(["status", "--short"])
    return [parse_status_line(line) for line in output.splitlines() if line.strip()]


def require_branch(mode: str) -> None:
    if mode == "ci":
        return
    branch = run_git(["branch", "--show-current"])
    if branch != TARGET_BRANCH:
        fail(f"current branch must be {TARGET_BRANCH}, got {branch or '<detached>'}")


def require_commits() -> None:
    log = run_git(["log", "--oneline", "--all"])
    for commit, subject in REQUIRED_COMMITS.items():
        if commit not in log or subject not in log:
            fail(f"missing required commit: {commit} {subject}")


def require_release_files() -> None:
    missing = [path for path in REQUIRED_RELEASE_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required release file(s): " + ", ".join(missing))


def require_tag_checklist() -> None:
    text = (ROOT / "docs/release/tag-checklist.md").read_text(encoding="utf-8")
    for marker in [
        "tag_status: pending_manual_owner_action",
        "target_tag: v0.1.0-mvp",
        "accepted_commit:",
        "reason: tag creation requires explicit owner approval",
        "push_status: not_pushed",
    ]:
        if marker not in text:
            fail(f"tag checklist missing marker: {marker}")


def require_no_tracked_env() -> None:
    tracked = run_git(["ls-files"])
    hits = [
        path
        for path in tracked.splitlines()
        if Path(path).name == ".env" or path.endswith("/.env")
    ]
    if hits:
        fail("tracked env file(s) are forbidden: " + ", ".join(hits))


def require_no_forbidden_root_paths() -> None:
    found = [path for path in FORBIDDEN_ROOT_PATHS if (ROOT / path).exists()]
    if found:
        fail("forbidden root path(s) exist: " + ", ".join(found))


def require_no_new_migrations(status_paths: list[str]) -> None:
    hits = [
        path
        for path in status_paths
        if any(marker in path for marker in MIGRATION_MARKERS)
    ]
    if hits:
        fail("migration changes are forbidden in Phase 7: " + ", ".join(hits))


def is_allowed_phase7_path(path: str) -> bool:
    return path in ALLOWED_PRECOMMIT_PATHS or path.startswith(ALLOWED_PRECOMMIT_PREFIXES)


def require_precommit_boundaries() -> None:
    paths = git_status_paths()
    require_no_new_migrations(paths)

    forbidden = []
    unexpected = []
    env_hits = []
    for path in paths:
        if not path:
            continue
        name = Path(path).name
        if path in ALLOWED_PRECOMMIT_PATHS:
            continue
        if name == ".env" or path.endswith("/.env"):
            env_hits.append(path)
        if path.startswith(FORBIDDEN_PRECOMMIT_PREFIXES):
            forbidden.append(path)
        elif not is_allowed_phase7_path(path):
            unexpected.append(path)

    if env_hits:
        fail("env file changes are forbidden: " + ", ".join(env_hits))
    if forbidden:
        fail("app/infra changes are forbidden in Phase 7 pre-commit mode: " + ", ".join(forbidden))
    if unexpected:
        fail("unexpected pre-commit change(s): " + ", ".join(unexpected))


def require_clean_worktree() -> None:
    output = run_git_raw(["status", "--short"]).strip()
    if output:
        fail("git status must be clean in final mode:\n" + output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("pre-commit", "final", "ci"),
        default="pre-commit",
        help="release-freeze validation mode",
    )
    args = parser.parse_args()

    require_branch(args.mode)
    require_commits()
    require_release_files()
    require_tag_checklist()
    require_no_tracked_env()
    require_no_forbidden_root_paths()

    if args.mode == "pre-commit":
        require_precommit_boundaries()
    elif args.mode == "final":
        require_clean_worktree()

    print(f"PASS: release freeze validation ({args.mode})")


if __name__ == "__main__":
    main()
