#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "docs/architecture/overview.md",
    "docs/architecture/system-context.md",
    "docs/architecture/data-flow.md",
    "docs/architecture/module-boundaries.md",
    "docs/adr/0001-tech-stack.md",
    "docs/adr/0002-p0-platform-strategy.md",
    "docs/adr/0003-gitops-lite-delivery.md",
    "docs/adr/0004-signal-quality-gate.md",
    "docs/adr/0005-ui-information-architecture.md",
    "docs/audits/0001-implementation-plan-audit.md",
    "docs/audits/0002-security-and-token-audit.md",
    "docs/audits/0003-ui-ux-audit.md",
    "docs/runbooks/local-startup.md",
    "docs/runbooks/rollback.md",
    "docs/runbooks/troubleshooting.md",
    "docs/runbooks/platform-credentials.md",
    "docs/runbooks/git-branch-protection.md",
    "docs/testing/test-plan.md",
    "docs/testing/test-report.md",
    "docs/testing/coverage-summary.md",
    "docs/release/v0.1.0-mvp-release-notes.md",
    "docs/release/tag-checklist.md",
]

ADR_REQUIRED = [
    "Context",
    "Decision",
    "Alternatives",
    "Consequences",
    "Rollback / Revisit condition",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def main() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required docs: " + ", ".join(missing))

    for adr in sorted((ROOT / "docs/adr").glob("*.md")):
        text = adr.read_text(encoding="utf-8")
        for marker in ADR_REQUIRED:
            if marker not in text:
                fail(f"{adr} missing ADR marker: {marker}")

    branch_doc = (ROOT / "docs/runbooks/git-branch-protection.md").read_text(encoding="utf-8")
    if "@owner must be replaced by the actual GitHub username or team before branch protection is enforced." not in branch_doc:
        fail("git branch protection runbook missing CODEOWNERS placeholder warning")

    print("PASS: docs validation")


if __name__ == "__main__":
    main()
