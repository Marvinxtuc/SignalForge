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

## Phase 3 Connector Abstraction Checklist

Status: PASS.

- Connector base contract tests: PASS
- Connector registry tests: PASS
- Disabled connector tests: PASS
- Mock connector tests: PASS
- `scripts/validate_connector_abstraction.py`: PASS
- `scripts/validate_backend_api.py`: PASS
- No-secrets validation: PASS
- `POST /api/projects/{project_id}/collect` supports only `mock`, `disabled_only`, and `safe_disabled`: PASS
- Real platform connectors unavailable until Phase 4: PASS

Phase 3 is not Reddit/Product Hunt real access. Phase 4 owns P0 Connectors, Phase 5 owns Processing Pipeline, and Phase 6 owns Frontend MVP.

## Phase 4 P0 Connectors Checklist

Status: PASS.

- RedditConnector exists: PASS
- ProductHuntConnector exists: PASS
- Missing Reddit credentials degrade to disabled: PASS
- Missing Product Hunt token degrades to disabled: PASS
- Reddit 401/403 maps to `permission_limited`: PASS
- Product Hunt 401/403 maps to `permission_limited`: PASS
- Reddit 429 maps to `rate_limited`: PASS
- Product Hunt 429 or explicit quota/rate error maps to `rate_limited`: PASS
- Mocked Reddit keyword/subreddit/comment normalization preserves `source_url`: PASS
- Mocked Product Hunt product/comment normalization preserves `source_url`: PASS
- Reddit deleted/removed body text is not retained: PASS
- Token values are absent from logs, API responses, reports, docs, and `raw_payload`: PASS
- `reddit`, `product_hunt`, and `p0_real` collect modes are supported: PASS
- CI uses mocked responses only and requires no real token: REQUIRED
- Manual smoke is local/manual only: REQUIRED
- Manual smoke default does not write `raw_items`: REQUIRED
- Product Hunt default API use is non-commercial unless Product Hunt grants permission: REQUIRED
- X / Discord remain unimplemented: REQUIRED
- Phase 4 does not create `signals`, `clusters`, or `opportunities`: REQUIRED
- Phase 5 owns Processing Pipeline: REQUIRED
- Phase 6 owns Frontend MVP: REQUIRED
- Phase 4 is not final MVP acceptance: REQUIRED

## Phase 5 Processing Pipeline Checklist

Status: PASS.

- Processing tests: PASS
- `scripts/validate_processing_pipeline.py`: PASS
- isolated raw-only validation project: PASS
- raw_items process into signals: PASS
- high value signals `>= 2`: PASS
- high value definition is `pain_level >= 70` and `signal_confidence >= 60`: PASS
- `source_url` preserved in signals and top high value signals: PASS
- PII / wallet / seed phrase suspicious content redacted before classification and embeddings: PASS
- fallback classifier available: PASS
- LLM JSON failure falls back without crashing: PASS
- score fields clamped to 0-100 before persistence: PASS
- deterministic mock embedding is 1536-dimensional and stable across runs: PASS
- embeddings persist to pgvector: PASS
- clusters created or updated: PASS
- opportunities created or updated: PASS
- archived/manual opportunity fields are not overwritten: PASS
- Signal Quality Gate summary complete: PASS
- repeated processing is idempotent for signals, embeddings, cluster links, opportunities, and high value counts: PASS
- CI uses mock LLM, mock embedding, and fallback only: REQUIRED
- Real LLM / embedding smoke is optional manual only: REQUIRED
- Signal Inbox / Dashboard / Opportunity Board remain unimplemented: REQUIRED
- X / Discord remain unimplemented: REQUIRED
- Phase 5 is not final MVP acceptance: REQUIRED

## Later Phase Items

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
