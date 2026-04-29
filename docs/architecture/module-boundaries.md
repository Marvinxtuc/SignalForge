# Module Boundaries

Status: PHASE_3_CONNECTOR_ABSTRACTION_PASS
Phase: Phase 3 Connector Abstraction

This document records module boundaries through Phase 3 Connector Abstraction and later phases. It does not represent final MVP acceptance.

## Planned Boundaries

- API: project, keyword, signal, cluster, opportunity, report, and settings endpoints.
- Connectors: Reddit, Product Hunt, and demo/mock only in P0.
- Processing Pipeline: cleaning, redaction, dedupe, LLM JSON validation, fallback, embeddings, clustering, and opportunity scoring.
- Web: Signal Inbox first, then Dashboard, Opportunity Board, Logs, Settings.
- Governance: CI, SOP, docs, acceptance reports, rollback runbook.

Phase -1 creates only governance assets and does not create business modules.

## Phase 0 Boundary

Phase 0 may create `apps/api`, `apps/web`, `infra`, and `scripts/wait_for_services.py`.

Phase 0 must not create:

- Connectors
- Processing Pipeline
- Business database models
- Signal Inbox
- Dashboard
- Opportunity Board
- Logs or Settings business pages

## Phase 1 Boundary

Phase 1 may create only the data model layer required for:

- `raw_items`
- `signals`
- `clusters`
- `opportunities`
- migrations
- demo seed data
- data validation

The required data path is `raw_items -> signals -> clusters -> opportunities`.

`source_url` is the evidence traceability baseline. The model layer must preserve source evidence so later review, clustering, and opportunity workflows can trace back to the original item.

Phase 1 must not implement:

- Business APIs
- Connectors
- Processing pipeline jobs
- Frontend product UI
- Production collection logic

Phase 2 Backend API owns business API implementation for projects, keywords, signals, clusters, opportunities, reports, and settings.

## Phase 2 Boundary

Phase 2 may implement:

- Backend API routes for projects, keywords, collection jobs, collection logs, signals, clusters, opportunities, reports, and settings.
- Pydantic schemas, service-layer CRUD, pagination, filtering, and unified error responses.
- API tests and backend API validation.
- Settings status reads that do not return `encrypted_payload`, token, or secret values.
- Reports generated only from existing database records.

Phase 2 collection behavior is intentionally degraded: `POST /api/projects/{project_id}/collect` may create a `pending` job and explanatory log, but it must not execute a connector or create `raw_items`.

Phase 2 must not implement:

- Connector abstraction or platform connectors.
- Reddit or Product Hunt API calls.
- Processing Pipeline jobs, LLM calls, embedding provider calls, or clustering algorithms.
- Frontend MVP pages such as Signal Inbox, Dashboard, or Opportunity Board.
- X or Discord implementation.

## Phase 3 Boundary

Phase 3 may implement:

- Connector interface contracts and normalized result types.
- Mock connector behavior for local deterministic checks.
- Disabled connector behavior for unavailable real platforms.
- Connector registry behavior for approved abstraction modes.
- Connector abstraction tests and validation.

Phase 3 `POST /api/projects/{project_id}/collect` behavior is limited to `mock`, `disabled_only`, and `safe_disabled`. It must not perform real Reddit or Product Hunt API calls.

Phase 3 must not implement:

- Reddit real connector implementation.
- Product Hunt real connector implementation.
- Production credential use or external platform API calls.
- Processing Pipeline jobs, LLM calls, embedding provider calls, or clustering algorithms.
- Frontend MVP pages such as Signal Inbox, Dashboard, or Opportunity Board.
- X or Discord implementation.

Real platform connectors are unavailable until Phase 4.

## Later Boundaries

- Phase 4 implements P0 Connectors for Reddit and Product Hunt.
- Phase 5 implements Processing Pipeline.
- Phase 6 implements Frontend MVP.
