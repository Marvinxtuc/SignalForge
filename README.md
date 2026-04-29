# SignalForge

Status: Phase 3 Connector Abstraction validated

SignalForge is a local-first VOC Radar MVP. The MVP goal is to prove that the system can surface high-value, actionable user demand signals, not to maximize collection volume or platform coverage.

## Current Phase

This repository is currently in Phase 3: Connector Abstraction validated.

Phase 0 Infrastructure is recorded as PASS. Phase 1 Data Model is recorded as PASS. Phase 2 Backend API is recorded as PASS. Phase 3 is limited to connector interfaces, normalized connector result types, mock/disabled connector behavior, registry behavior, tests, validation, and documentation.

Not included in this phase:

- Reddit or Product Hunt real connector implementation
- Processing Pipeline
- Frontend MVP or UI pages
- Celery task logic
- Real platform collection
- LLM or embedding provider calls

Phase 3 owns Connector Abstraction only. Phase 4 owns P0 Connectors. Phase 5 owns Processing Pipeline. Phase 6 owns Frontend MVP.

Phase 3 does not connect to Reddit or Product Hunt. Real platform connectors are unavailable until Phase 4.

`POST /api/projects/{project_id}/collect` supports only the Phase 3 connector abstraction modes `mock`, `disabled_only`, and `safe_disabled`. Any real platform connector request must remain unavailable until Phase 4.

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

## Next Phase

Phase 4 P0 Connectors require explicit approval. Do not implement Reddit/Product Hunt real connectors, processing, frontend MVP, X, or Discord in Phase 3.

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
