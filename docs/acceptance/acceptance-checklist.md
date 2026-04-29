# Acceptance Checklist

Status: PASS_WITH_MANUAL_ACTIONS
Phase: Phase 7 Testing / Acceptance / Release Freeze

This checklist records local/mock MVP acceptance and Phase 7 release freeze readiness. It does not record real platform or real provider smoke as PASS.

## Final MVP Local / Mock Must Pass

- Docker Compose up: PASS
- API health OK: PASS
- Web accessible: PASS
- Demo seed OK: PASS
- Mock collection OK: PASS
- Reddit connector degraded or success in mocked/local mode: PASS
- Product Hunt connector degraded or success in mocked/local mode: PASS
- raw_items -> signals OK: PASS
- signals -> clusters OK: PASS
- clusters -> opportunities OK: PASS
- Signal Inbox visible: PASS
- High value signals highlighted: PASS
- Open Source link visible: PASS
- CSV export OK: PASS
- Markdown export OK: PASS
- No token leak: PASS
- Docs complete: PASS
- Final acceptance report present: PASS

CI does not require real platform tokens. Real platform acceptance is local/manual acceptance and remains NOT_EXECUTED / pending token until explicitly run.

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

## Phase 6 Frontend MVP Checklist

Status: PASS.

- Web npm build: PASS
- `scripts/validate_frontend_mvp.py --require-http`: PASS
- Required pages `/`, `/signals`, `/dashboard`, `/opportunities`, `/logs`, `/settings`, `/reports`: PASS
- Signal Inbox visible: PASS
- Dashboard visible: PASS
- Opportunity Board visible: PASS
- Logs visible: PASS
- Settings visible without `encrypted_payload`: PASS
- Reports visible with markdown and csv controls: PASS
- Open Source evidence text visible: PASS
- High value signals highlighted: PASS
- Frontend API client only calls SignalForge backend-relative paths: PASS
- Forbidden endpoints absent from frontend source: PASS
- No token-like values in frontend source: PASS
- Forbidden real execution options absent: PASS
- Localhost HTTP smoke: PASS
- Phase 6 is not final MVP acceptance: REQUIRED

## Phase 7 Final Acceptance / Release Freeze Checklist

Status: PASS_WITH_MANUAL_ACTIONS.

- MVP local/mock acceptance: PASS
- Release readiness: PASS_WITH_MANUAL_ACTIONS
- Final acceptance report finalized: PASS
- Test report finalized: PASS
- Coverage summary finalized: PASS
- README final state updated: PASS
- Manual smoke not misrepresented as PASS: PASS
- Real Reddit smoke: NOT_EXECUTED / pending token
- Real Product Hunt smoke: NOT_EXECUTED / pending token
- Real LLM smoke: NOT_EXECUTED / pending token
- Real embedding smoke: NOT_EXECUTED / pending token
- Production deployment: NOT_INCLUDED
- Auth / multi-user: NOT_INCLUDED
- X connector: NOT_INCLUDED
- Discord connector: NOT_INCLUDED
- Commercial Product Hunt authorization review: PENDING_MANUAL_OWNER_ACTION
- Tag creation: pending_manual_owner_action
- Branch protection enforcement: pending_manual_owner_action
- `@owner` replacement: pending_manual_owner_action

Phase 7 freezes `v0.1.0-mvp` local/mock readiness. It does not create a tag, push a tag, configure branch protection, run real smoke, or claim production readiness.

## Manual Owner Actions

These items are not completed acceptance items:

- Replace `@owner` with the actual GitHub user or team.
- Configure branch protection.
- Create local tag `v0.1.0-mvp` only after explicit owner approval.
- Push tag only after separate explicit owner approval.
- Run real Reddit smoke with token if required.
- Run real Product Hunt smoke with token if required.
- Run real LLM smoke if required.
- Run real embedding smoke if required.
- Complete Product Hunt commercial authorization review before commercial use.

## Post-MVP Backlog

These items are outside v0.1.0 local/mock acceptance:

- Optional X Connector.
- Optional Discord Connector.
- Auth and multi-user support.
- Production deployment.
- Billing / SaaS administration.
- Real platform smoke acceptance.
- Real LLM / embedding provider acceptance.
- Product Hunt commercial authorization review completion.

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
