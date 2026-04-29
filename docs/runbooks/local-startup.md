# Local Startup Runbook

Status: PHASE_3_CONNECTOR_ABSTRACTION_PASS
Phase: Phase 3 Connector Abstraction

Phase 0 provides local runtime services for infrastructure smoke testing only.

## Services

- API: http://localhost:8000
- API health: http://localhost:8000/health
- Web: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Start

```bash
docker compose -f infra/docker-compose.yml up -d
```

## Wait for readiness

```bash
python3 scripts/wait_for_services.py
```

## Stop

```bash
docker compose -f infra/docker-compose.yml down
```

## Governance validation

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
```

Phase 0 does not include business APIs, connectors, processing pipeline, Signal Inbox, or data models.

## Phase 1 Data Model Local Execution

Status: PASS after container-mode validation.

Start infrastructure first:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
```

Run Phase 1 migration, seed, and validation:

```bash
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_migrations.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
docker compose -f infra/docker-compose.yml run --rm api alembic downgrade base
```

Expected Phase 1 data path:

```text
raw_items -> signals -> clusters -> opportunities
```

`source_url` is the evidence traceability baseline and must be available for review of seeded signal evidence.

Phase 1 implements only models, migrations, seed, and validation. Phase 2 implements business APIs.

## Phase 2 Backend API Local Execution

Phase 2 runs backend API tests against the Phase 1 schema and demo seed. It does not run connectors, processing pipeline jobs, LLM calls, embedding provider calls, or frontend MVP flows.

Start infrastructure:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
```

Prepare data and run API validation:

```bash
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
```

Stop services:

```bash
docker compose -f infra/docker-compose.yml down
```

Expected Phase 2 API boundary:

- `POST /api/projects/{project_id}/collect` creates a pending job only.
- Reports are generated from local database records only.
- Settings status responses never expose `encrypted_payload` or token values.
- `source_url` remains visible for signal and report evidence.

## Phase 3 Connector Abstraction Local Execution

Status: PASS.

Phase 3 validates connector abstraction only. It does not run Reddit or Product Hunt real platform connectors. Real platform connectors are unavailable until Phase 4.

Start infrastructure:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
```

Prepare data and run connector abstraction checks:

```bash
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api pytest /app/tests/test_connector_base.py /app/tests/test_connector_registry.py /app/tests/test_disabled_connector.py /app/tests/test_mock_connector.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
python3 scripts/validate_no_secrets.py
```

Stop services:

```bash
docker compose -f infra/docker-compose.yml down
```

Expected Phase 3 boundary:

- `POST /api/projects/{project_id}/collect` supports only `mock`, `disabled_only`, and `safe_disabled`.
- Real Reddit and Product Hunt connectors remain unavailable until Phase 4.
- Processing Pipeline remains unavailable until Phase 5.
- Frontend MVP remains unavailable until Phase 6.
