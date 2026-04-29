# Module Boundaries

Status: PHASE_5_PROCESSING_PIPELINE_PASS
Phase: Phase 5 Processing Pipeline

This document records module boundaries through Phase 5 Processing Pipeline and later phases. It does not represent final MVP acceptance.

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

## Phase 4 Boundary

Phase 4 may implement:

- RedditConnector through official API/OAuth only.
- ProductHuntConnector through official GraphQL API only.
- Env-only credential resolution for Reddit and Product Hunt.
- HTTP client behavior with timeouts, token redaction, safe response snapshots, and mocked CI responses.
- Rate limit, permission-limited, disabled, and failed connector states.
- Collection executor integration for `reddit`, `product_hunt`, and `p0_real` execution modes.
- Collection logs and `raw_items` writes from normalized P0 connector items.
- Optional local/manual smoke scripts guarded by `SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true`.

Phase 4 must keep CI mocked. CI must not require real Reddit or Product Hunt tokens. Manual smoke defaults to read-only preview and must not write `raw_items` unless `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true` is also set.

Phase 4 must not implement:

- X or Discord connectors.
- Processing Pipeline jobs, LLM calls, embedding provider calls, or clustering algorithms.
- Frontend MVP pages such as Signal Inbox, Dashboard, or Opportunity Board.
- Browser automation, scraping, simulated login, automated posting, commenting, or messaging.
- New database tables or Alembic migrations.
- Token persistence in `platform_credentials.encrypted_payload`, logs, API responses, exports, docs, or connector `raw_payload`.

Reddit deletion handling and rate limit handling are mandatory. Deleted or removed content must not retain deleted body text. Product Hunt default API usage is non-commercial unless Product Hunt grants permission.

Phase 4 is P0 Connectors only and is not final MVP acceptance.

## Phase 5 Boundary

Phase 5 may implement:

- Processing Pipeline modules for cleaning, redaction, language detection, noise filtering, duplicate collapse, fallback classification, mock LLM behavior, mock embedding generation, clustering, opportunity scoring, and Signal Quality Gate.
- Processing API endpoints for project processing and processing summary.
- Mock-only processing tests and `scripts/validate_processing_pipeline.py`.
- Optional manual LLM and embedding smoke scripts guarded by explicit env flags.

Phase 5 CI must use mock LLM, mock embedding, and deterministic fallback. CI must not require real LLM or embedding provider tokens.

Phase 5 must not implement:

- Signal Inbox, Dashboard, Opportunity Board, or other Frontend MVP pages.
- X or Discord connectors.
- Reddit, Product Hunt, X, Discord, real LLM, or real embedding provider calls during CI.
- Platform content model training.
- New database tables, Alembic migrations, `processing_jobs`, or `processing_logs`.
- Token persistence in logs, API responses, reports, docs, or raw payload fields.

Phase 5 is Processing Pipeline only and is not final MVP acceptance.

## Later Boundaries

- Phase 6 implements Frontend MVP.
