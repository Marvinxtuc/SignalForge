# SignalForge Personal Production v1 Blocking Issue Register

## Release Gate Status

`BLOCKED_EXTERNAL_SMOKE_URL_MISSING`

This file does not approve production SaaS launch, does not authorize auto-merge, and must not be converted into a merge approval.

## Task Judgment

- Agent name: Blocking Issue Register Agent.
- Scope: release blocker register only.
- PASS / FAIL: FAIL for full `READY_TO_MERGE`; local business workflow remains PASS.
- Decision: one unresolved blocker exists because external smoke could not run without `SIGNALFORGE_EXTERNAL_SMOKE_URL`.

## Confirmed Facts

- Repository: `/Users/marvin.x/Desktop/SignalForge`.
- Branch: `feature/personal-production-v1`.
- Local gate evidence passed: Docker config/build/up, service readiness, Alembic upgrade, API pytest, web build, no-secrets, frontend MVP, personal workflow, report business value, source traceability, and Playwright E2E.
- External smoke command was guarded and exited `2` with `SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set`.
- No auto-merge was performed.

## Blocking Issue

```text
Issue ID:
PPV1-BLOCKER-001

Detected by:
External Smoke Agent / Main coordinator

Detected timestamp:
2026-04-30 Asia/Shanghai

Affected report/check:
external_smoke_report.md / scripts/validate_external_smoke.py

Severity:
P1

Issue status:
OPEN

Description:
External smoke validation could not run because SIGNALFORGE_EXTERNAL_SMOKE_URL is unset. Local business workflow passed, but external reachability and same-origin external API behavior are not verified.

Evidence:
Command exited 2: if [ -n "$SIGNALFORGE_EXTERNAL_SMOKE_URL" ]; then python3 scripts/validate_external_smoke.py --url "$SIGNALFORGE_EXTERNAL_SMOKE_URL" --check-api; else echo 'SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set'; exit 2; fi
stdout: SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set

Required fix or acceptance:
Provide an approved external URL and rerun python3 scripts/validate_external_smoke.py --url "$SIGNALFORGE_EXTERNAL_SMOKE_URL" --check-api with redacted output. Until then, PR body must use READY_TO_MERGE: false and final decision must be BUSINESS_WORKFLOW_PASS_EXTERNAL_SMOKE_FAIL_READY_TO_MERGE_BLOCKED.

Owner:
Release owner / external environment owner

Resolution evidence:
Pending.
```

## Non-Blocking Checks

- Security: no real secret values found by `python3 scripts/validate_no_secrets.py`; Settings UI no longer renders concrete secret env names.
- Data workflow: connector abstraction validator passed with `EXPECTED_MOCK_ITEMS = 5`.
- QA: local personal production workflow passed.

## Rollback

If the blocker is resolved, update this file with the successful external smoke command and close the issue. If the file itself must be removed, deletion requires approval.
