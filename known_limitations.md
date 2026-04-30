# SignalForge Personal Production v1 Known Limitations

## Release Gate Status

`REVIEWED_WITH_EXTERNAL_SMOKE_BLOCKER`

This file documents accepted limitations for Personal Production v1 only. It does not approve production SaaS launch, auto-merge, or deployment.

## Task Judgment

- Agent name: Known Limitations Agent.
- Scope: limitations register only.
- PASS / FAIL: PASS for local personal production limitations review; BLOCKED for external smoke readiness.
- Decision: limitations are explicit and reviewable; unresolved external smoke remains in `blocking_issue.md`.

## Confirmed Facts

- Local business workflow passed through API and Playwright E2E.
- Settings is an env-status workspace only; it does not save or display secret values.
- No new credential encryption dependency, credential key, credential CRUD, or migration was added.
- External smoke did not run because `SIGNALFORGE_EXTERNAL_SMOKE_URL` is missing.

## Limitation Register

| Area | Limitation | Impact | Accepted for personal production? | Evidence/owner |
| --- | --- | --- | --- | --- |
| Authentication | No production SaaS authentication or authorization is implemented for this release. | Suitable only for controlled personal/local usage, not public SaaS. | Accepted for personal production only. | Security/CTO review; owner: release owner |
| External access | External URL smoke is missing. | Blocks `READY_TO_MERGE: true` until verified. | Not accepted as merge-ready; tracked as blocker. | `external_smoke_report.md`, `blocking_issue.md` |
| Data/backup | Seed and downgrade paths can destroy local/project data if misused. | Requires backup discipline before destructive commands. | Accepted with operational caution. | `data_workflow_report.md`; owner: data workflow/release owner |
| Monitoring/logging | No production-grade monitoring, alerting, or incident process. | Personal production only; no SaaS SLO claim. | Accepted for personal production only. | QA/security reports |
| Scale/performance | No scale/load testing beyond local workflow validation. | Not approved for high-volume or multi-user workloads. | Accepted for personal production only. | QA report |
| SaaS readiness | Not approved as production SaaS. | Prevents SaaS launch claim. | Required boundary. | CTO/release owner |
| Merge automation | Auto-merge is not approved. | Manual merge decision required after blockers resolved. | Required boundary. | Git/Release report |

## Decision Rules

- External smoke blocker must remain open until an approved URL passes `scripts/validate_external_smoke.py --check-api`.
- Accepted limitations apply only to Personal Production v1 and must be revisited before any SaaS launch claim.
- This file cannot override `blocking_issue.md`.

## Rollback

If this limitations register needs to be removed, deletion requires approval. If tracked, content rollback is `git restore -- known_limitations.md`.
