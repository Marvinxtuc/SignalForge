# Local Startup Runbook

Status: PHASE_6_FRONTEND_MVP_PASS
Phase: Phase 6 Frontend MVP

Phase 6 uses the local runtime services plus frontend build and validation gates and is recorded as PASS. It is not Phase 7 final MVP acceptance.

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
- Frontend MVP is available after Phase 6 PASS.

## Phase 4 P0 Connectors Local Execution

Status: PASS.

Phase 4 validates Reddit and Product Hunt connectors. CI and default local validation use mocked responses only and do not require real platform tokens.

Start infrastructure:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
```

Prepare data and run mocked P0 connector checks:

```bash
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
docker compose -f infra/docker-compose.yml run --rm api pytest /app/tests/test_reddit_connector.py /app/tests/test_product_hunt_connector.py /app/tests/test_p0_connector_degradation.py /app/tests/test_p0_connector_rate_limits.py /app/tests/test_p0_connector_no_token_leak.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py --no-token-leak
```

Optional manual smoke is local/manual only:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_reddit_smoke.py
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_product_hunt_smoke.py
```

Manual smoke defaults to preview/status only and must not write `raw_items`. To allow writes, explicitly set:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true
```

Stop services:

```bash
docker compose -f infra/docker-compose.yml down
```

Expected Phase 4 boundary:

- Reddit and Product Hunt are P0 connectors.
- X and Discord remain unimplemented.
- CI uses mocked responses only and requires no real token.
- Product Hunt default API use is non-commercial unless Product Hunt grants permission.
- Reddit deleted/removed content handling and rate limit parsing are mandatory.
- Phase 5 owns Processing Pipeline.
- Phase 6 owns Frontend MVP.
- Phase 4 is not final MVP acceptance.

## Phase 6 Frontend MVP Local Execution

Status: PASS.

Start infrastructure if HTTP smoke is desired:

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
```

Build and validate the frontend:

```bash
cd apps/web
npm install --no-audit --no-fund --package-lock=false
npm run build
cd ../..
python3 scripts/validate_frontend_mvp.py
```

If `http://localhost:3000` is reachable, `scripts/validate_frontend_mvp.py` checks:

```text
/
/signals
/dashboard
/opportunities
/logs
/settings
/reports
```

Expected Phase 6 boundary:

- Required frontend pages exist.
- Open Source evidence text and high value markers are present.
- Settings does not render `encrypted_payload`.
- Reports expose markdown and csv controls.
- Frontend requests go through the SignalForge backend API client only.
- No real execution options or token-like values appear in frontend source.

## Phase 7 Release Freeze Local Execution

Status: RELEASE_FREEZE_READY.

Phase 7 does not add product functionality. It validates that the MVP can be started, tested, documented, rolled back, and prepared for owner-controlled release tagging.

Run release governance checks:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
python3 scripts/validate_final_acceptance.py
python3 scripts/validate_release_freeze.py --mode pre-commit
```

Run full local regression:

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

After the Phase 7 commit exists, run:

```bash
python3 scripts/validate_release_freeze.py --mode final
```

Expected Phase 7 boundary:

- No new product functionality.
- No new database schema or migration.
- No real platform or provider smoke unless the owner explicitly authorizes it.
- Tag creation remains pending manual owner action.
- `v0.1.0-mvp` release notes, rollback runbook, and tag checklist are ready for owner review.
- Phase 7 final MVP acceptance remains not started.
