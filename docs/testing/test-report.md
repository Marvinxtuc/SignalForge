# Test Report

Status: NOT_STARTED
Phase: Phase -1 Governance Bootstrap
Current workstream: Phase 1 Data Model
This document does not represent final MVP acceptance.

## Phase Results

- Phase -1 Governance Bootstrap: PASS
- Phase -1 SOP Marker Rectification: PASS
- Phase 0 Infrastructure: PASS
- Phase 1 Data Model: PASS

## Phase 0 Local Results

- Governance validation: PASS
- Python syntax check: PASS
- Forbidden path check: PASS
- Docker Compose config: PASS
- Docker Compose build: PASS
- Docker Compose up -d: PASS
- wait_for_services.py: PASS
- Docker Compose down: PASS

Notes:

- Docker runtime was provided through Colima.
- The Phase 0 Web shell dependency `next` was updated to 16.2.4 after build output reported a security warning for the original 15.1.4 baseline.

No final MVP tests have been run.

## Phase 1 Data Model Results

Phase 1 validation completed through API container mode:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
docker compose -f infra/docker-compose.yml config
docker compose -f infra/docker-compose.yml build
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

Phase 1 evidence:

- Governance validation: PASS
- Docker Compose config: PASS
- Docker Compose build: PASS
- Docker Compose up -d: PASS
- wait_for_services.py: PASS
- Migration up: PASS
- validate_migrations.py: PASS
- Demo seed first run: PASS
- Demo seed second run: PASS
- validate_data_model.py: PASS
- Migration down: PASS
- Docker Compose down: PASS
- Data validation confirmed `raw_items -> signals -> clusters -> opportunities`.
- `source_url` remains the evidence traceability baseline.

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
