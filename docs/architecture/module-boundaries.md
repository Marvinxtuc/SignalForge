# Module Boundaries

Status: PHASE_2_BACKEND_API_VALIDATED
Phase: Phase 2 Backend API

This document records module boundaries for Phase 2 Backend API and later phases. It does not represent final MVP acceptance.

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

## Later Boundaries

- Phase 3 implements Connector Abstraction.
- Phase 4 implements P0 Connectors for Reddit and Product Hunt.
- Phase 5 implements Processing Pipeline.
- Phase 6 implements Frontend MVP.
