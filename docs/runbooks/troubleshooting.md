# Troubleshooting Runbook

Status: PHASE_6_FRONTEND_MVP_PASS
Phase: Phase 6 Frontend MVP

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
- Frontend MVP is available after Phase 6 PASS.

If validation requires real platform tokens or external API access, treat it as scope drift.

## Phase 4 P0 connector tests fail

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest /app/tests/test_reddit_connector.py /app/tests/test_product_hunt_connector.py /app/tests/test_p0_connector_degradation.py /app/tests/test_p0_connector_rate_limits.py /app/tests/test_p0_connector_no_token_leak.py
```

Expected Phase 4 test behavior:

- Tests use mocked Reddit and Product Hunt responses only.
- Real Reddit or Product Hunt tokens are not required.
- X and Discord remain unimplemented.
- No Processing Pipeline, LLM, embedding provider, or frontend MVP behavior is tested.

Do not fix Phase 4 test failures by adding X/Discord connectors, browser automation, scraping, LLM calls, embedding calls, frontend code, new migrations, or token persistence.

## Phase 4 connector validation fails

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py --no-token-leak
python3 scripts/validate_no_secrets.py
```

Expected Phase 4 validation behavior:

- `reddit`, `product_hunt`, and `p0_real` modes are validated with mocked responses.
- Missing tokens degrade safely.
- Permission and rate limit conditions produce readable collection logs.
- `signals`, `clusters`, and `opportunities` are not created by connector execution.
- Tokens do not appear in logs, API responses, reports, docs, or connector `raw_payload`.

## Phase 4 manual smoke is disabled

Manual smoke must not run unless the operator sets:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true
```

If the flag is missing, the manual smoke scripts should exit with a disabled explanation. This is expected and is not a CI failure.

Manual smoke does not write `raw_items` unless this flag is also set:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true
```

If manual smoke reports Product Hunt permission limits, record the result as `permission_limited` unless the connector itself crashes or leaks a token. Product Hunt default API use is non-commercial unless Product Hunt grants permission.

If manual smoke reports Reddit rate limits, record `rate_limited` and do not retry aggressively. Reddit rate limit headers and deleted/removed content handling are mandatory Phase 4 safety checks.

## Phase 5 processing tests fail

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest /app/tests/test_processing_cleaner.py /app/tests/test_processing_redactor.py /app/tests/test_processing_classifier.py /app/tests/test_processing_fallback.py /app/tests/test_processing_embedding.py /app/tests/test_processing_clustering.py /app/tests/test_signal_quality_gate.py /app/tests/test_processing_pipeline.py
```

Expected Phase 5 test behavior:

- Tests use mock LLM, mock embedding, and fallback only.
- Real LLM or embedding provider tokens are not required.
- Redaction happens before classification, summaries, embeddings, and clustering.
- Repeated processing remains idempotent.
- Signal Inbox, Dashboard, Opportunity Board, X, and Discord remain unimplemented.

Do not fix Phase 5 test failures by adding frontend UI, X/Discord connectors, external platform calls, real provider CI dependencies, new migrations, or token persistence.

## Phase 5 processing validation fails

Run:

```bash
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_processing_pipeline.py
python3 scripts/validate_no_secrets.py
```

Expected Phase 5 validation behavior:

- Validation creates or uses an isolated raw-only project.
- The project starts without signals, embeddings, clusters, or opportunities.
- The pipeline proves `raw_items -> signals -> embeddings -> clusters -> opportunities`.
- Signal Quality Gate reports high value signals, fallback counts, cluster coverage, opportunities, and top evidence with `source_url`.
- CI uses mock LLM and mock embedding only.

If validation requires real provider tokens or external platform access, treat it as scope drift.

## Phase 5 manual LLM or embedding smoke is disabled

Manual LLM smoke must not run unless the operator sets:

```bash
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true
```

Manual embedding smoke must not run unless the operator sets:

```bash
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true
```

If either flag is missing, the manual smoke scripts should exit with a disabled explanation. This is expected and is not a CI failure. Manual smoke must not print provider tokens or write docs containing provider responses.

## Phase 6 frontend build fails

Run:

```bash
cd apps/web
npm install --no-audit --no-fund --package-lock=false
npm run build
```

Expected Phase 6 build behavior:

- Next.js builds the frontend without requiring real platform tokens.
- Build-time code uses `NEXT_PUBLIC_API_BASE_URL` or the default local SignalForge backend URL only.
- Build failures must not be fixed by changing backend business logic, migrations, connector behavior, or provider credentials.

## Phase 6 frontend validation fails

Run:

```bash
python3 scripts/validate_frontend_mvp.py
```

Expected Phase 6 validation behavior:

- Required routes exist: `/`, `/signals`, `/dashboard`, `/opportunities`, `/logs`, `/settings`, and `/reports`.
- Open Source evidence text is present.
- High value signal markers are present.
- Settings does not render `encrypted_payload`.
- Reports expose markdown and csv controls.
- Frontend source calls only the centralized SignalForge backend API client.
- Forbidden real execution options are absent: `reddit_real`, `product_hunt_real`, `p0_real`, `real_llm`, `real_embedding`, `x_real`, and `discord_real`.
- Token-like values are absent from frontend source.

If `http://localhost:3000` is not reachable, the HTTP smoke portion is skipped by default. Use `--require-http` only when a local web server is expected to be running.

Do not mark Phase 7 final MVP acceptance complete from Phase 6 validation alone.
