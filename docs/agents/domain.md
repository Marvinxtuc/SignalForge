# SignalForge Domain Notes For Agents

Status: consumer rules for repo-local Hermes/Codex skills.

Read these docs before making domain, architecture, PRD, issue, or triage recommendations:

- `README.md`
- `docs/architecture/overview.md`
- `docs/architecture/module-boundaries.md`
- `docs/architecture/data-flow.md`
- `docs/adr/`
- `docs/testing/test-plan.md`
- `docs/runbooks/rollback.md`

## Canonical domain path

SignalForge is a local-first VOC Radar MVP. The validated demand-signal path is:

`raw_items -> signals -> embeddings -> clusters -> opportunities`

Source evidence traceability is mandatory. Preserve `source_url` from source evidence through
signal review, clustering, opportunity evaluation, and reports.

## Scope and risk reminders

- P0 platforms are Reddit and Product Hunt.
- X is P1 and Discord is P2.
- CI must use mocked platform/provider behavior.
- Real platform, real LLM, and real embedding smoke checks are local/manual only and require
  explicit environment flags.
- Manual platform smoke must not write `raw_items` unless
  `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true` is explicitly set.
- Tokens, secrets, encrypted payloads, and credential values must not appear in logs, docs,
  API responses, exports, reports, or raw payload fields.
- Production deployment, auth, billing, SaaS commercialization, and release tag creation are
  outside the current repo-local skill pilot unless separately approved.

