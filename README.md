# SignalForge

Status: Phase 4 P0 Connectors PASS

SignalForge is a local-first VOC Radar MVP. The MVP goal is to prove that the system can surface high-value, actionable user demand signals, not to maximize collection volume or platform coverage.

## Current Phase

This repository is currently in Phase 4: P0 Connectors PASS.

Phase 0 Infrastructure is recorded as PASS. Phase 1 Data Model is recorded as PASS. Phase 2 Backend API is recorded as PASS. Phase 3 Connector Abstraction is recorded as PASS. Phase 4 is limited to P0 connectors for Reddit and Product Hunt, mocked CI validation, optional local/manual real-platform smoke scripts, and documentation.

Not included in this phase:

- Processing Pipeline
- Frontend MVP or UI pages
- Celery task logic
- X or Discord connectors
- CI real platform collection
- LLM or embedding provider calls
- Browser automation, scraping, simulated login, automated posting, commenting, or messaging

Phase 4 owns P0 Connectors only. Phase 5 owns Processing Pipeline. Phase 6 owns Frontend MVP.

CI uses mocked Reddit and Product Hunt responses only and does not require real platform tokens. Manual smoke is local/manual only and is disabled unless `SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true` is set. Manual smoke does not write `raw_items` unless `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true` is also set.

`POST /api/projects/{project_id}/collect` keeps the Phase 3 modes `mock`, `disabled_only`, and `safe_disabled`, and Phase 4 adds P0 modes `reddit`, `product_hunt`, and `p0_real`. Missing credentials, permission limits, and rate limits must degrade into readable collection logs and must not crash jobs.

Phase 4 is not final MVP acceptance.

## Platform Scope

- P0: Reddit and Product Hunt
- P1: X
- P2: Discord

CI must not depend on real platform tokens. Real Reddit and Product Hunt checks are local/manual acceptance items and must be recorded in the final acceptance report later.

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

## Next Phase

Phase 5 Processing Pipeline requires explicit approval. Do not implement processing, LLM classification, embedding generation, clustering, frontend MVP, X, or Discord in Phase 4.

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
