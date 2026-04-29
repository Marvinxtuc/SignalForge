# Troubleshooting Runbook

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

## Validation Fails

Run the failing script directly and inspect the printed missing files or failed checks.

## Commit Fails

If Git user.name or user.email is missing, do not modify global Git config. Record `commit pending manual owner action`.

## CI Placeholder Confusion

Docker, Data, and Acceptance gates are Phase -1 placeholders only. Real checks will be enabled in later phases.

## Docker build fails

- Confirm Docker Desktop or the Docker daemon is running.
- Run `docker compose -f infra/docker-compose.yml config` before build.
- Check network access for base images and package installs.

## Port already in use

Phase 0 defaults:

- API: 8000
- Web: 3000
- PostgreSQL: 5432
- Redis: 6379

Stop conflicting local services or adjust ports in a later approved change.

## API health fails

Run:

```bash
docker compose -f infra/docker-compose.yml logs api
```

Expected health payload:

```json
{"status":"ok","service":"signalforge-api","phase":"phase-0-infrastructure"}
```

## Web is not accessible

Run:

```bash
docker compose -f infra/docker-compose.yml logs web
```

The Phase 0 web app is a static infrastructure shell and does not call business APIs.

## PostgreSQL is not ready

Run:

```bash
docker compose -f infra/docker-compose.yml logs postgres
```

The `pgvector/pgvector:pg16` image is used and `infra/postgres-init.sql` initializes the `vector` extension.

## Redis is not ready

Run:

```bash
docker compose -f infra/docker-compose.yml logs redis
```

The Redis healthcheck uses `redis-cli ping`.

## Phase 1 migration fails

Run:

```bash
docker compose -f infra/docker-compose.yml logs postgres
docker compose -f infra/docker-compose.yml run --rm api alembic current
docker compose -f infra/docker-compose.yml run --rm api alembic history
```

Record the failure as Phase 1 Data Model requires scoped rectification. Do not mark final MVP acceptance complete.

## Phase 1 seed fails

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
```

Check that migrations have run before seed execution. Seed data must support the `raw_items -> signals -> clusters -> opportunities` path.

## Phase 1 data validation fails

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py
```

Confirm that seeded signals preserve `source_url`. `source_url` is the evidence traceability baseline for Phase 1 and later acceptance review.

## Phase 2 API tests fail

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest
```

Confirm migrations and demo seed have run before tests:

```bash
docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py
```

Do not fix Phase 2 test failures by adding connectors, processing jobs, LLM calls, embedding provider calls, or frontend code.

## Phase 2 backend validation fails

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
```

Expected Phase 2 behavior:

- API reads and writes local database records only.
- `POST /api/projects/{project_id}/collect` returns connector execution as unavailable until a later phase.
- Settings responses do not include `encrypted_payload`.
- Reports and signals preserve `source_url`.

If the failure is related to connector execution, external API access, LLM calls, or frontend behavior, treat it as scope drift rather than a Phase 2 requirement.

## Phase 3 connector abstraction tests fail

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest /app/tests/test_connector_base.py /app/tests/test_connector_registry.py /app/tests/test_disabled_connector.py /app/tests/test_mock_connector.py
```

Expected Phase 3 behavior:

- Connector contracts return normalized results.
- Registry behavior is deterministic.
- Disabled connectors fail safely.
- Mock connectors use local deterministic behavior only.
- No Reddit or Product Hunt real platform API calls are attempted.

Do not fix Phase 3 test failures by adding real Reddit/Product Hunt connector logic, processing jobs, LLM calls, embedding provider calls, or frontend code.

## Phase 3 connector abstraction validation fails

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py
python3 scripts/validate_no_secrets.py
```

Expected Phase 3 collect behavior:

- `POST /api/projects/{project_id}/collect` supports only `mock`, `disabled_only`, and `safe_disabled`.
- Real platform connectors are unavailable until Phase 4.
- Processing Pipeline is unavailable until Phase 5.
- Frontend MVP is unavailable until Phase 6.

If validation requires real platform tokens or external API access, treat it as scope drift.
