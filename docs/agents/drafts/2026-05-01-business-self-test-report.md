# SignalForge Full Business Self-Test Report

Date: 2026-05-01
Branch: `feature/personal-production-v1`
Mode: subagent execution
Scope: local/mock full business self-test plus manual smoke gate check

## Task Judgment

SignalForge local/mock business path is functionally passing end to end.

The only failed gate is release-freeze branch validation: `validate_release_freeze.py --mode pre-commit` expects `feature/mvp-p0`, but the current branch is `feature/personal-production-v1`.

Manual real-platform, real LLM, and real embedding smoke did not run because the explicit enable flags and credentials are unset. This is a correct gated result, not a product runtime failure.

## Current Goal

Verify whether the overall business workflow runs locally:

`infra -> migrations -> seed -> API -> connectors -> processing -> frontend -> reports -> governance`

Also enumerate every non-passing point, give a solution path, and provide follow-up retest commands.

## Confirmed Facts

- Docker Compose config/build/startup completed successfully.
- API, Web, Postgres, and Redis became ready through `scripts/wait_for_services.py`.
- Backend/data validations passed, including migrations, seed data, API, connector abstraction, P0 connector mock behavior, processing pipeline, and pytest.
- Business E2E validations passed against `http://localhost:8000`.
- Frontend build, frontend MVP HTTP smoke, and Playwright mocked UI E2E passed.
- Manual smoke scripts ran in gated mode and reported no provider call because flags and credentials are unset.
- Docker services were stopped after the test run with `docker compose -f infra/docker-compose.yml down`.
- Worktree had pre-existing untracked files and test/build-generated output was not cleaned.

## Commands Run

### Infra / Governance Agent

| Command | Result | Exit | Key output |
|---|---:|---:|---|
| `git status --short --branch` | PASS | 0 | `feature/personal-production-v1`; untracked files present |
| `docker compose -f infra/docker-compose.yml config` | PASS | 0 | Services rendered: `api`, `postgres`, `redis`, `web` |
| `docker compose -f infra/docker-compose.yml build` | PASS | 0 | `infra-api:latest` and `infra-web:latest` built; buildx warning observed |
| `docker compose -f infra/docker-compose.yml up -d` | PASS | 0 | API/Web running, Postgres healthy |
| `python3 scripts/wait_for_services.py` | PASS | 0 | `PASS: all Phase 0 services are ready` |
| `python3 scripts/validate_docs.py` | PASS | 0 | `PASS: docs validation` |
| `python3 scripts/validate_acceptance.py` | PASS | 0 | `PASS: acceptance validation` |
| `python3 scripts/validate_no_secrets.py` | PASS | 0 | `PASS: no secrets validation` |
| `python3 scripts/validate_final_acceptance.py` | PASS | 0 | `PASS: final acceptance validation` |
| `python3 scripts/validate_release_freeze.py --mode pre-commit` | FAIL | 1 | `current branch must be feature/mvp-p0, got feature/personal-production-v1` |

### Backend / Data Agent

| Command | Result | Exit | Key output |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head` | PASS | 0 | PostgreSQL migration context initialized |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py` | PASS | 0 | `PASS: demo data seeded` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py` | PASS | 0 | `data model validation succeeded for 5 demo raw_items` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py` | PASS | 0 | `backend API validation succeeded` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py` | PASS | 0 | `connector abstraction validation succeeded` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py` | PASS | 0 | `P0 connector validation succeeded` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py --no-token-leak` | PASS | 0 | `P0 connector validation succeeded` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_processing_pipeline.py` | PASS | 0 | `raw_items -> signals -> embeddings -> clusters -> opportunities` verified |
| `docker compose -f infra/docker-compose.yml run --rm api pytest` | PASS | 0 | `128 passed in 0.87s` |

### Business E2E Agent

| Command | Result | Exit | Key output |
|---|---:|---:|---|
| `API_BASE_URL=http://localhost:8000 python3 scripts/validate_personal_workflow.py` | PASS | 0 | mock collect/process, signals, opportunities, reports, cleanup passed |
| `API_BASE_URL=http://localhost:8000 python3 scripts/validate_source_traceability.py` | PASS | 0 | signal list/detail and reports preserve `source_url` and `recommended_action` |
| `API_BASE_URL=http://localhost:8000 python3 scripts/validate_report_business_value.py` | PASS | 0 | high-value signals, opportunities, markdown/csv reports passed |

### Frontend Agent

| Command | Result | Exit | Key output |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml run --rm web npm run build` | PASS | 0 | `Compiled successfully`; static pages generated |
| `python3 scripts/validate_frontend_mvp.py --require-http` | PASS | 0 | `frontend MVP validation succeeded` |
| `cd apps/web && npm run test:e2e` | PASS | 0 | `2 passed` |

Note: Playwright installs API mocks in the test, so it proves the UI workflow but not live backend behavior. Live backend behavior is covered by the Business E2E Agent commands.

### Manual Smoke Agent

Relevant env gate status:

```text
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=UNSET
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=UNSET
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=UNSET
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=UNSET
REDDIT_CLIENT_ID=UNSET
REDDIT_CLIENT_SECRET=UNSET
REDDIT_USER_AGENT=UNSET
PRODUCT_HUNT_TOKEN=UNSET
LLM_API_KEY=UNSET
OPENAI_API_KEY=UNSET
ANTHROPIC_API_KEY=UNSET
EMBEDDING_API_KEY=UNSET
LLM_BASE_URL=UNSET
EMBEDDING_MODEL=UNSET
```

| Command | Result | Exit | Key output |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_reddit_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `write_enabled: False` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_product_hunt_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `write_enabled: False` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_llm_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `real_provider_called: False` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_embedding_smoke.py` | NOT_EXECUTED | 0 | `SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true is required`; no provider call made |

### Cleanup

| Command | Result | Exit | Key output |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml down` | PASS | 0 | API/Web/Postgres/Redis containers and network removed |

## PASS / FAIL / NOT_EXECUTED Matrix

| Area | Status | Evidence |
|---|---:|---|
| Docker Compose config | PASS | compose config rendered services |
| Docker build | PASS | API/Web images built |
| Local services readiness | PASS | `wait_for_services.py` passed |
| Migrations | PASS | `alembic upgrade head` passed |
| Demo seed | PASS | `seed_demo_data.py` passed |
| Data model | PASS | `validate_data_model.py` passed |
| Backend API | PASS | `validate_backend_api.py` passed |
| Connector abstraction | PASS | `validate_connector_abstraction.py` passed |
| P0 connector mock and no-token leak | PASS | both `validate_p0_connectors.py` commands passed |
| Processing pipeline | PASS | `validate_processing_pipeline.py` passed |
| API pytest suite | PASS | `128 passed` |
| Business E2E | PASS | personal workflow, traceability, report business value passed |
| Frontend build and smoke | PASS | web build and frontend MVP validation passed |
| Playwright UI E2E | PASS | `2 passed`; mocked API evidence |
| Governance docs/no-secrets/final acceptance | PASS | validation scripts passed |
| Release freeze pre-commit gate | FAIL | branch mismatch |
| Manual Reddit smoke | NOT_EXECUTED | flag and credentials unset |
| Manual Product Hunt smoke | NOT_EXECUTED | flag and credentials unset |
| Manual LLM smoke | NOT_EXECUTED | flag and credentials unset |
| Manual embedding smoke | NOT_EXECUTED | flag and credentials unset |

## Non-Passing Items

### F-001 Release Freeze Branch Mismatch

Status: FAIL

Command:

```bash
python3 scripts/validate_release_freeze.py --mode pre-commit
```

Observed:

```text
FAIL: current branch must be feature/mvp-p0, got feature/personal-production-v1
```

Impact:

- Blocks release-freeze pre-commit gate.
- Does not invalidate the local/mock business flow, which otherwise passed.

Likely cause:

- The release-freeze script encodes `feature/mvp-p0` as the expected branch.
- Current work is on `feature/personal-production-v1`.

Recommended solution:

- Decide the authoritative release branch for this work.
- If `feature/personal-production-v1` is correct, update the release-freeze branch policy in a separate approved change.
- If `feature/mvp-p0` is correct, switch or recreate the work on that branch only after owner approval and clean worktree review.

Retest path:

```bash
python3 scripts/validate_release_freeze.py --mode pre-commit
```

Rollback:

- No code changed for this failure.
- If a future branch-policy patch is made, roll it back with `git revert <commit>`.

### N-001 Manual Real Smoke Not Executed

Status: NOT_EXECUTED

Observed:

- Real platform smoke flags are unset.
- Real LLM/embedding smoke flags are unset.
- Required credentials are unset.
- Scripts exited successfully in gated mode without real provider calls.

Impact:

- Local/mock MVP is validated.
- Real Reddit, Product Hunt, LLM, and embedding provider acceptance remains pending.

Recommended solution:

- Provide credentials through the approved local secret path.
- Explicitly enable the required smoke flag only for the intended provider.
- Keep `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE` unset unless raw item writes are explicitly approved.

Retest path:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_reddit_smoke.py
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_product_hunt_smoke.py
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_llm_smoke.py
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_embedding_smoke.py
```

Rollback:

- Unset smoke flags and stop services.
- If real platform writes are later approved and executed, database cleanup requires a separate owner-approved plan.

### R-001 Worktree and Generated Output Risk

Status: RESIDUAL_RISK

Observed:

- Pre-existing untracked files: `AGENTS.md`, `apps/web/test-results/`, `current_state_report.md`, `docs/agents/`, `token_behavior_report.md`.
- Frontend build/test produced or left `apps/web/next-env.d.ts` modified.

Impact:

- Does not block local/mock self-test.
- Must be reconciled before commit/release review.

Recommended solution:

- Review each untracked or generated path and classify as keep/stage/ignore/remove.
- Do not delete or revert anything without owner approval.

Retest path:

```bash
git status --short --branch
python3 scripts/validate_release_freeze.py --mode pre-commit
```

Rollback:

- For generated file churn, use an approved revert or regeneration policy.
- For untracked files, owner must approve deletion or staging.

## Follow-Up Test Path

Minimal retest after fixing branch/worktree release gate:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
python3 scripts/validate_final_acceptance.py
python3 scripts/validate_release_freeze.py --mode pre-commit
```

Full local/mock retest:

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
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py --no-token-leak
docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_processing_pipeline.py
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm web npm run build
python3 scripts/validate_frontend_mvp.py --require-http
API_BASE_URL=http://localhost:8000 python3 scripts/validate_personal_workflow.py
API_BASE_URL=http://localhost:8000 python3 scripts/validate_source_traceability.py
API_BASE_URL=http://localhost:8000 python3 scripts/validate_report_business_value.py
cd apps/web && npm run test:e2e
cd ../..
docker compose -f infra/docker-compose.yml down
```

## Residual Risks

- Release-freeze gate remains failing until branch policy and current branch are aligned.
- Real provider acceptance remains pending and must not be represented as PASS.
- Current worktree is not clean and includes untracked governance/report files.
- Docker build emitted a buildx plugin warning even though build passed.
- Database state was intentionally mutated by migration/seed/E2E commands; no volume deletion or destructive cleanup was performed.

## Rollback Method

- Report file rollback: remove or revert `docs/agents/drafts/2026-05-01-business-self-test-report.md`.
- Runtime rollback: services were already stopped with `docker compose -f infra/docker-compose.yml down`.
- Code rollback: no business code, schema, API, dependency, config, hook, CI, deployment, secret, or permission changes were made.
- Database reset or volume deletion is not included and requires separate approval because it is destructive to local data.
