# SignalForge

Status: Phase 0 Infrastructure

SignalForge is a local-first VOC Radar MVP. The MVP goal is to prove that the system can surface high-value, actionable user demand signals, not to maximize collection volume or platform coverage.

## Current Phase

This repository is currently in Phase 0: Infrastructure.

This phase creates the infrastructure skeleton for local startup. It includes a minimal FastAPI service, a minimal Next.js service, PostgreSQL with pgvector, Redis, Docker Compose, and service readiness checks.

Not included in this phase:

- Connector implementation
- Processing Pipeline
- UI pages
- Database models
- Business APIs
- Celery task logic

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

## Governance Validation

Run:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
```

Do not commit `.env` or real API credentials. `.env.example` must contain only variable names and empty values.

## Next Phase

Phase 1 Data Model may start only after Phase 0 is accepted.

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
