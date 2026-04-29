# Module Boundaries

Status: PHASE_1_DATA_MODEL_VALIDATED
Phase: Phase 1 Data Model

This document records module boundaries for Phase 1 Data Model and later phases. It does not represent final MVP acceptance.

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
