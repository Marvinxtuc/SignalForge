# Acceptance Checklist

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

This checklist is a skeleton and does not represent final MVP acceptance.

## Must Pass Later

- Docker Compose up
- API health OK
- Web accessible
- Demo seed OK
- Mock collection OK
- Reddit connector degraded or success
- Product Hunt connector degraded or success
- raw_items -> signals OK
- signals -> clusters OK
- clusters -> opportunities OK
- Signal Inbox visible
- High value signals highlighted
- Open Source link visible
- CSV export OK
- Markdown export OK
- No token leak
- Docs complete
- Final acceptance report present

CI does not require real platform tokens. Real platform acceptance is local/manual acceptance.

## Phase 0 Checklist

- Docker Compose config passes.
- Docker Compose build passes.
- Docker Compose up starts API, Web, PostgreSQL, and Redis.
- API `/health` returns `status: ok`.
- Web `/` is accessible.
- PostgreSQL socket readiness passes.
- Redis socket readiness passes.
- `scripts/wait_for_services.py` passes.
- Docker Compose down completes.

Phase 0 Docker Gate result: PASS.

## Phase 1 Data Model Checklist

Status: PASS after local container-mode validation.

- Migration up: PASS
- Migration down: PASS
- pgvector extension: PASS
- `embeddings.embedding` as `vector(1536)`: PASS
- 11 core tables: PASS
- raw_items unique/platform source URL constraints: PASS
- cluster_signals composite primary key: PASS
- demo seed idempotency: PASS
- data model validation: PASS
- Required data flow documented: `raw_items -> signals -> clusters -> opportunities`
- Evidence traceability baseline documented: `source_url`
- Phase 1 limited to models, migrations, seed, and validation.
- Phase 2 owns business API implementation.

## Phase 2 Backend API Checklist

Status: PASS.

- Health API reports Phase 2 status: PASS
- Projects CRUD: PASS
- Keywords CRUD: PASS
- Collection job pending creation without connector execution: PASS
- Collection logs list: PASS
- Signals list and `min_pain_level` filter: PASS
- Signal feedback and status updates: PASS
- Clusters list, detail, update, archive: PASS
- Opportunities list, detail, create, update, archive: PASS
- Markdown report export with `source_url`: PASS
- CSV report export with `source_url`: PASS
- Settings platform status: PASS
- Credential status excludes `encrypted_payload`: PASS
- API response token leak check: PASS
- Unified error response: PASS
- Pagination response: PASS
- pytest: PASS
- `scripts/validate_backend_api.py`: PASS
- Governance validation and no-secrets validation: PASS

Phase 2 is backend API only. Connector abstraction starts in Phase 3, P0 connectors start in Phase 4, processing starts in Phase 5, and frontend MVP starts in Phase 6.

## Later Phase Items

- Connector and product acceptance checks start in later phases.
- Signal Inbox and Opportunity Board start in Phase 6 Frontend MVP.

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
