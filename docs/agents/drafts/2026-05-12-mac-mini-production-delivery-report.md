# Mac Mini Owner-Only Local Production Delivery Report

Status: LOCAL_PRODUCTION_GO_WITH_REAL_PROVIDER_NO_GO

## Scope

- Included: Mac mini Docker production profile, owner-only auth, production lifecycle run audit,
  real-provider gates, localhost-only validation, backup/restore runbook, and local acceptance evidence.
- Not included: public internet production, tunnel, router forwarding, TLS/domain, multi-user SaaS,
  billing, X/Discord connectors, or unapproved real provider calls.

## Result

- Mac mini local production: GO
- Public internet production: NOT_INCLUDED
- Tunnel: NOT_STARTED
- Product Hunt commercial authorization: PENDING_MANUAL_OWNER_ACTION
- Real provider full production: NO-GO_REAL_PROVIDER until credentials and run-level owner approval exist.

## Evidence Summary

- Architecture Agent: PASS, see `docs/agents/drafts/2026-05-12-mac-mini-production-architecture.md`.
- Backend owner auth/lifecycle tests: PASS, `6 passed`.
- API regression: PASS, isolated compose migration + seed + full pytest, `134 passed`.
- Frontend build: PASS. Next 16 still warns that `middleware.ts` should migrate to `proxy.ts`.
- Frontend production lifecycle E2E: PASS, targeted Playwright test, `1 passed`.
- Production static safety: PASS with `python3 scripts/validate_mac_local_production.py --strict-env`.
- Production stack: PASS. Web binds to `127.0.0.1:3000`; API/Postgres/Redis are Docker-internal.
- In-app browser smoke: PASS. Login, project creation, production lifecycle run, and closeout were verified.
- Lifecycle audit: PASS. Closed smoke run recorded `preflight, collect, process, review, report, closeout`.
- Real-provider gate: PASS_NO_GO. Request stopped at preflight with missing approvals/env and no external calls.
- Backup/restore drill: PASS. Backup was restored into a temporary database, verified, then removed.
- No-secrets: PASS. `.env.production.local` is ignored and placeholder values are rejected by strict validation.

## Rollback

- Stop local production:
  `docker compose --env-file .env.production.local -f infra/docker-compose.production.yml down`
- Revert the implementation commit:
  `git revert <commit>`
- If database rollback is needed, restore from a verified backup only after owner confirmation.
- If smoke data should be removed, delete the smoke project/run through an approved cleanup path or restore from backup.

## Residual Items

- Real Reddit/Product Hunt/LLM/Embedding smoke is intentionally not executed because credentials and owner approval are absent.
- Product Hunt commercial authorization remains manual owner action.
- Public internet production is explicitly outside this phase.
- Next.js warns that `middleware.ts` is deprecated in favor of `proxy.ts`; runtime behavior and build pass.
