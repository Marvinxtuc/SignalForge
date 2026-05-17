# Mac Mini Local Production Acceptance

Status: EXECUTED_LOCAL_PRODUCTION_SMOKE

## Required Result

- Mac mini local production: GO
- Public internet production: NOT_INCLUDED
- Tunnel: NOT_STARTED
- Product Hunt commercial authorization: PENDING_MANUAL_OWNER_ACTION
- Real provider full production: NO-GO_REAL_PROVIDER until owner supplies credentials and approves a real run.

## Required Evidence

- Production compose validates local-only port exposure.
- Owner-only auth rejects unauthenticated Web/API access.
- Owner session can execute the production lifecycle.
- Lifecycle run records preflight, collect, process, review, report, and closeout.
- Real Reddit/Product Hunt smoke is recorded as `PASS_REAL`, `PERMISSION_LIMITED`,
  `RATE_LIMITED`, or `NO-GO_REAL_PROVIDER`.
- Real LLM/Embedding smoke is recorded as `PASS_REAL` or `NO-GO_REAL_PROVIDER`.
- Backup and restore drill is recorded.
- No secrets validation passes.

## Executed Evidence

- Production compose build/up: PASS. Web is published only as `127.0.0.1:3000->3000/tcp`;
  API/Postgres/Redis expose container ports only.
- Migration: PASS. Production stack upgraded through `0002_production_lifecycle_runs`.
- Owner auth negative checks: PASS. Unauthenticated `/signals` redirects to `/login`; unauthenticated
  `/api/health` returns `401 owner_auth_required`.
- In-app browser owner workflow: PASS. Browser logged in at `http://127.0.0.1:3000/login`, created
  project `个人生产 E2E`, opened `/production`, executed mock lifecycle, and observed closeout.
- Lifecycle record: PASS. Latest closed smoke run recorded
  `preflight, collect, process, review, report, closeout`.
- Real provider gate: PASS_NO_GO. A real-provider request without credentials/approval stopped at
  `no_go_real_provider` during preflight; no external provider call was made.
- Backup: PASS. Created `backups/signalforge-production-20260512T095257Z.dump`.
- Restore drill: PASS. Restored the backup into a temporary database and verified
  `production_lifecycle_runs` was readable, then removed the temporary database.
- No secrets: PASS. Local production env is ignored and strict validation now rejects `change-me`
  placeholder values.
- Tunnel check: PASS. No `cloudflared`, `trycloudflare`, or `ngrok` process detected.
- API regression: PASS. Full API pytest ran in an isolated compose project with migration + seed;
  `134 passed`.
- Frontend production lifecycle E2E: PASS. Playwright targeted test passed.

## No-Go

- Any public tunnel is running.
- API, Postgres, or Redis is host-published.
- `sf_token` is treated as production auth.
- Provider keys appear in logs, docs, reports, API responses, or raw payloads.
- Real platform write occurs without run-level owner approval.
