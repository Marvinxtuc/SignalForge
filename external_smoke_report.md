# SignalForge Personal Production v1 External Smoke Report

## Status

`BLOCKED/FAIL`

External smoke did not run because `SIGNALFORGE_EXTERNAL_SMOKE_URL` is not set. This is an external smoke blocker only; this report does not change or judge the local workflow gate.

## Task Judgment

- Agent name: External Smoke Agent.
- Scope: inspect external smoke prerequisites and update `external_smoke_report.md` only.
- Decision: external smoke is `BLOCKED/FAIL` until an approved external URL is provided.
- Network rule: no network smoke was run without `SIGNALFORGE_EXTERNAL_SMOKE_URL`.
- Merge rule: this report does not approve production SaaS launch, auto-merge, or `READY_TO_MERGE`.

## Current Goal

- Confirm whether the required external smoke URL is available.
- Confirm the expected external smoke command and validation targets.
- Record the blocked result with reproducible command evidence.

## Confirmed Facts

- Repository: `/Users/marvin.x/Desktop/SignalForge`.
- Branch: `feature/personal-production-v1`.
- Commit inspected: `a7e29c1`.
- Verification timestamp: `2026-04-30 08:40:41 CST`.
- Required environment variable `SIGNALFORGE_EXTERNAL_SMOKE_URL` was not set in this shell.
- `scripts/validate_external_smoke.py` exists and requires `--url`.
- With `--check-api`, the script validates same-origin API endpoints:
  - `/api/health`
  - `/api/projects?page_size=1`
  - `/api/settings/platforms`
- The script redacts `sf_token` in emitted URLs.
- `deploy_plan.md` records the expected external smoke flow: start an external tunnel, then run `python3 scripts/validate_external_smoke.py --url '<external-url-redacted>' --check-api`.

## Files Inspected

- `external_smoke_report.md`
- `scripts/validate_external_smoke.py`
- `deploy_plan.md`
- Repository status via `git status --short`

## Files Changed

- `external_smoke_report.md`

No app source, tests, workflows, package files, scripts, deployment files, secrets, or configuration files were modified.

## Commands Executed

| Command | Exit code | Stdout summary | Stderr summary |
| --- | ---: | --- | --- |
| `pwd && git status --short` | 0 | Printed repo path and showed existing dirty worktree, including many modified/untracked files. | None. |
| `rg -n "SIGNALFORGE_EXTERNAL_SMOKE_URL\|external smoke\|external_smoke\|smoke" -S .` | 0 | Found external smoke references, including `scripts/validate_external_smoke.py`, `deploy_plan.md`, and this report. | None. |
| `ls -la` | 0 | Listed repository root files. | None. |
| `sed -n '1,240p' external_smoke_report.md` | 0 | Read prior report template. | None. |
| `sed -n '1,220p' scripts/validate_external_smoke.py` | 0 | Confirmed external smoke script arguments, validation targets, and token redaction behavior. | None. |
| `sed -n '70,120p' deploy_plan.md` | 0 | Confirmed documented external tunnel and smoke command prerequisites. | None. |
| `if [ -n "$SIGNALFORGE_EXTERNAL_SMOKE_URL" ]; then echo 'SET'; else echo 'SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set'; exit 2; fi` | 2 | `SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set` | None. |
| `date '+%Y-%m-%d %H:%M:%S %Z'` | 0 | `2026-04-30 08:40:41 CST` | None. |
| `git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD` | 0 | `feature/personal-production-v1`, `a7e29c1` | None. |
| `rg -n "SIGNALFORGE_EXTERNAL_SMOKE_URL\|validate_external_smoke.py\|/api/health\|/api/projects\|/api/settings/platforms" scripts/validate_external_smoke.py deploy_plan.md external_smoke_report.md` | 0 | Confirmed prerequisite references and same-origin API targets. | None. |
| `sed -n '1,260p' external_smoke_report.md` | 0 | Confirmed updated report content. | None. |
| `awk 'index($0,"sf_token=") && index($0,"sf_token=<redacted>")==0 {print; bad=1} END {exit bad}' external_smoke_report.md` | 0 | No token leakage pattern found. | None. |
| `git diff --name-only -- external_smoke_report.md && git diff -- external_smoke_report.md` | 0 | Confirmed the diff is limited to `external_smoke_report.md`. | None. |

## PASS/FAIL

FAIL: external smoke is blocked because the required URL is missing.

Not executed:

- External page reachability check.
- External no-HTTP-500 check.
- External same-origin `/api/health` check.
- External same-origin `/api/projects?page_size=1` check.
- External same-origin `/api/settings/platforms` check.

## Risk Points

- A missing external URL prevents any evidence-based statement about external reachability.
- Prior external smoke PASS references in other reports may be stale and were not treated as current evidence.
- Temporary tunnel URLs are not stable release infrastructure.
- External smoke validates reachability only; it does not prove SaaS-grade availability, auth, monitoring, incident response, or long-term production readiness.

## Next Action

Provide an approved current value for `SIGNALFORGE_EXTERNAL_SMOKE_URL`, then rerun:

```bash
if [ -n "$SIGNALFORGE_EXTERNAL_SMOKE_URL" ]; then python3 scripts/validate_external_smoke.py --url "$SIGNALFORGE_EXTERNAL_SMOKE_URL" --check-api; else echo 'SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set'; exit 2; fi
```

Record only redacted URL/token evidence. Do not mark external smoke PASS until the command exits `0`.

## Rollback

```bash
git restore -- external_smoke_report.md
```
