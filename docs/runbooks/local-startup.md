# Local Startup Runbook

Status: PHASE_1_DATA_MODEL_VALIDATED
Phase: Phase 1 Data Model

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
