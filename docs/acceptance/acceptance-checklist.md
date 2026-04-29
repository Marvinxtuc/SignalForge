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

## Later Phase Items

- Data migration checks start in Phase 1 Data Model.
- Business APIs start after Phase 1.
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
