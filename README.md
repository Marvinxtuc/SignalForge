# SignalForge

Status: Phase 7 Release Readiness PASS_WITH_MANUAL_ACTIONS

SignalForge is a local-first VOC Radar MVP. The MVP goal is to prove that the system can surface high-value, actionable user demand signals, not to maximize collection volume or platform coverage.

## Current Phase

This repository is currently in Phase 7: Testing / Acceptance / Release Freeze.

Phase -1 Governance Bootstrap is recorded as PASS. Phase 0 Infrastructure is recorded as PASS. Phase 1 Data Model is recorded as PASS. Phase 2 Backend API is recorded as PASS. Phase 3 Connector Abstraction is recorded as PASS. Phase 4 P0 Connectors is recorded as PASS. Phase 5 Processing Pipeline is recorded as PASS with mock LLM, mock embedding, deterministic fallback, Signal Quality Gate, and mock-only CI validation. Phase 6 Frontend MVP is recorded as PASS for Signal Inbox, Dashboard, Opportunity Board, Logs, Settings, Reports, frontend build, and frontend MVP validation.

Phase 7 final acceptance status:

- MVP local/mock acceptance: PASS
- Real platform smoke: NOT_EXECUTED / pending token
- Real LLM smoke: NOT_EXECUTED / pending token
- Real embedding smoke: NOT_EXECUTED / pending token
- Release readiness: PASS_WITH_MANUAL_ACTIONS
- Target tag: `v0.1.0-mvp`
- Tag status: pending_manual_owner_action
- Production deployment: NOT_INCLUDED

Not included in this phase:

- Celery task logic
- X or Discord connectors
- CI real platform collection
- CI real LLM or embedding provider calls
- Browser automation, scraping, simulated login, automated posting, commenting, or messaging
- Production deployment
- Auth / multi-user
- Billing or SaaS commercialization
- Release tag creation without explicit owner approval

Phase 4 owns P0 Connectors only. Phase 5 owns Processing Pipeline. Phase 6 owns Frontend MVP. Phase 7 owns final testing, acceptance, and release freeze. Phase 7 does not imply production readiness.

CI uses mocked Reddit and Product Hunt responses only and does not require real platform tokens. Manual smoke is local/manual only and is disabled unless `SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true` is set. Manual smoke does not write `raw_items` unless `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true` is also set.

`POST /api/projects/{project_id}/collect` keeps the Phase 3 modes `mock`, `disabled_only`, and `safe_disabled`, and Phase 4 adds P0 modes `reddit`, `product_hunt`, and `p0_real`. Missing credentials, permission limits, and rate limits must degrade into readable collection logs and must not crash jobs.

Phase 4 is not final MVP acceptance.

Phase 5 is not final MVP acceptance. It must prove `raw_items -> signals -> embeddings -> clusters -> opportunities` through mock-first and fallback-first processing, not through real provider dependency.

Phase 6 is not final MVP acceptance. It must prove the frontend can render the approved MVP pages, highlight high value signals, preserve Open Source evidence links, expose markdown/csv report controls, keep settings credential-safe, and use only the SignalForge backend API client.

## Platform Scope

- P0: Reddit and Product Hunt
- P1: X
- P2: Discord

CI must not depend on real platform tokens. Real Reddit and Product Hunt checks are local/manual acceptance items and are recorded as NOT_EXECUTED / pending token in the final acceptance report until explicitly run by the owner.

## Phase 0 Local Startup

Docker Compose file:

```bash
infra/docker-compose.yml
```

Start services:

```bash
docker compose -f infra/docker-compose.yml up -d
```

Check readiness:

```bash
python3 scripts/wait_for_services.py
```

API health:

```bash
curl http://localhost:8000/health
```

Web:

```bash
open http://localhost:3000
```

Stop services:

```bash
docker compose -f infra/docker-compose.yml down
```

Phase 0 validates PostgreSQL and Redis readiness at the socket level, and initializes the PostgreSQL `vector` extension. Business tables and migrations start in Phase 1 Data Model.

## Phase 1 Data Model Commands

Phase 1 local execution uses API container mode so migration, seed, and validation do not depend on host Python packages:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_migrations.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
docker compose -f infra/docker-compose.yml run --rm api alembic downgrade base
docker compose -f infra/docker-compose.yml down
```

The Phase 1 data flow baseline is:

```text
raw_items -> signals -> clusters -> opportunities
```

`source_url` is the evidence traceability baseline and must be preserved from source evidence through signal review and opportunity evaluation.

## Phase 2 Backend API Commands

Phase 2 uses the existing Phase 1 schema and demo seed data. It exposes backend APIs only; it does not execute connectors, processing jobs, LLM calls, embedding generation, or frontend product UI.

Start infrastructure, apply migrations, seed demo data, and run API checks:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
docker compose -f infra/docker-compose.yml down
```

Expected Phase 2 behavior:

- `GET /health` reports `phase-2-backend-api`.
- Project, keyword, signal, cluster, opportunity, collection, report, and settings APIs read or update local database state only.
- `POST /api/projects/{project_id}/collect` creates a pending job and does not execute a connector.
- Reports preserve `source_url` and must not expose token or credential payload data.

## Governance Validation

Run:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
```

Do not commit `.env` or real API credentials. `.env.example` must contain only variable names and empty values.

## Phase 3 Connector Abstraction Commands

Phase 3 local validation completed through API container mode:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
python3 scripts/validate_no_secrets.py
docker compose -f infra/docker-compose.yml down
```

Expected Phase 3 behavior:

- Connector abstraction tests cover base connector contracts, registry behavior, disabled connectors, and mock connector behavior.
- `POST /api/projects/{project_id}/collect` accepts only `mock`, `disabled_only`, and `safe_disabled` behavior.
- Real platform connectors are unavailable until Phase 4.
- No final MVP completion is implied by Phase 3 validation.

## Phase 4 P0 Connector Commands

Phase 4 validates Reddit and Product Hunt connectors with mocked responses in CI. Real tokens are not required for CI, pytest, or validation scripts.

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py --no-token-leak
docker compose -f infra/docker-compose.yml down
```

Expected Phase 4 behavior:

- Reddit and Product Hunt are P0 connectors.
- X and Discord remain unimplemented.
- CI uses mocked responses only and does not require real tokens.
- Reddit deletion handling must not retain deleted or removed body text.
- Reddit rate limit headers must be parsed and surfaced safely.
- Product Hunt API use is non-commercial by default unless Product Hunt grants permission.
- Manual smoke is local/manual only and defaults to no `raw_items` writes.
- Tokens must not appear in logs, API responses, reports, docs, or connector `raw_payload`.
- Phase 5 owns Processing Pipeline. Phase 6 owns Frontend MVP.

Manual real-platform smoke is optional:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_reddit_smoke.py
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_product_hunt_smoke.py
```

To allow manual smoke to write `raw_items`, explicitly add:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true
```

## Phase 5 Processing Pipeline Commands

Phase 5 validates processing with mock LLM, mock embedding, deterministic fallback, and isolated raw-only validation data. CI does not require real LLM or embedding tokens.

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_processing_pipeline.py
docker compose -f infra/docker-compose.yml down
```

Expected Phase 5 behavior:

- `raw_items` can be processed into `signals`.
- High value signals use `pain_level >= 70` and `signal_confidence >= 60`.
- Redaction happens before classification, summaries, embeddings, and clustering.
- Mock embeddings are deterministic, 1536-dimensional, and do not use provider calls.
- LLM JSON failure falls back without crashing processing.
- Clusters and opportunities are created or updated from processed signals.
- Signal Quality Gate reports processing coverage, high value ratio, fallback counts, cluster coverage, opportunity count, and top high value signals with `source_url`.
- Repeated processing is idempotent for signals, embeddings, cluster links, opportunities, and high value signal counts.
- Real LLM and embedding smoke are optional local/manual checks only.
- Signal Inbox, Dashboard, Opportunity Board, X, and Discord remain unimplemented.

Manual provider smoke is optional and disabled by default:

```bash
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_llm_smoke.py
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_embedding_smoke.py
```

## Phase 6 Frontend MVP Commands

Phase 6 validates frontend build and static acceptance boundaries. It does not run Phase 7 final acceptance.

```bash
cd apps/web
npm install --no-audit --no-fund --package-lock=false
npm run build
cd ../..
python3 scripts/validate_frontend_mvp.py
```

If `http://localhost:3000` is reachable, `scripts/validate_frontend_mvp.py` also performs optional HTTP smoke checks for `/`, `/signals`, `/dashboard`, `/opportunities`, `/logs`, `/settings`, and `/reports`.

Expected Phase 6 behavior:

- Required frontend pages exist.
- The UI includes Open Source / 打开来源 evidence text and a High Value / 高价值 marker.
- The frontend UI is localized to Chinese while preserving backend enum values, URL paths, and API request parameters.
- Settings does not render `encrypted_payload`.
- Reports expose markdown and csv export controls.
- The frontend API client accepts only SignalForge backend-relative paths.
- Forbidden real execution options remain absent: `reddit_real`, `product_hunt_real`, `p0_real`, `real_llm`, `real_embedding`, `x_real`, and `discord_real`.
- No token-like values are present in frontend source.

## Phase 7 Final Acceptance / Release Freeze

Phase 7 freezes the local/mock MVP for owner review. It does not add features, create production deployment, create a release tag, or execute real platform/provider smoke by default.

Final acceptance command set:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
python3 scripts/validate_final_acceptance.py
python3 scripts/validate_release_freeze.py --mode pre-commit
```

Full local regression remains Docker Compose based:

```bash
docker compose -f infra/docker-compose.yml config
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_processing_pipeline.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm web npm run build
python3 scripts/validate_frontend_mvp.py --require-http
docker compose -f infra/docker-compose.yml down
```

Manual smoke status for this release freeze:

- Real Reddit smoke: NOT_EXECUTED / pending token
- Real Product Hunt smoke: NOT_EXECUTED / pending token
- Real LLM smoke: NOT_EXECUTED / pending token
- Real embedding smoke: NOT_EXECUTED / pending token

Manual smoke is not counted as PASS until explicitly authorized, supplied with tokens, executed, and recorded.

Release freeze is for `v0.1.0-mvp` local/mock MVP readiness only. Production deployment, branch protection enforcement, tag creation, and real smoke remain manual owner actions.

Manual owner actions:

- Replace `@owner` with the actual GitHub user or team.
- Configure branch protection.
- Create local tag `v0.1.0-mvp` only after explicit owner approval.
- Push tag only after separate explicit owner approval.
- Run real Reddit smoke with token if required.
- Run real Product Hunt smoke with token if required.
- Run real LLM smoke if required.
- Run real embedding smoke if required.
- Complete Product Hunt commercial authorization review before commercial use.

Post-MVP backlog:

- Optional X Connector.
- Optional Discord Connector.
- Auth and multi-user support.
- Production deployment.
- Billing / SaaS administration.
- Real platform smoke acceptance.
- Real LLM / embedding provider acceptance.
- Product Hunt commercial authorization review completion.

## Canonical v2.1 Phase Markers

- `phase_-1_governance_bootstrap`
- `phase_0_infrastructure`
- `phase_1_data_model`
- `phase_2_backend_api`
- `phase_3_connector_abstraction`
- `phase_4_p0_connectors`
- `phase_5_processing_pipeline`
- `phase_6_frontend_mvp`
- `phase_7_testing_acceptance_release_freeze`
