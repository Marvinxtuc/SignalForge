# Coverage Summary

Status: PASS_WITH_MANUAL_ACTIONS
Phase: Phase 7 Testing / Acceptance / Release Freeze

This summary records local/mock MVP coverage for `v0.1.0-mvp`. It does not claim real platform smoke, real LLM smoke, real embedding smoke, production deployment, or commercial readiness.

## Phase Coverage Status

- Phase -1 Governance Bootstrap: PASS
- Phase -1 SOP Marker Rectification: PASS
- Phase 0 Infrastructure: PASS
- Phase 1 Data Model: PASS
- Phase 2 Backend API: PASS
- Phase 3 Connector Abstraction: PASS
- Phase 4 P0 Connectors: PASS
- Phase 5 Processing Pipeline: PASS
- Phase 6 Frontend MVP: PASS
- Phase 7 Testing / Acceptance / Release Freeze: PASS_WITH_MANUAL_ACTIONS

## Automated Coverage Summary

- Governance scripts: PASS
- Docs-as-code validation: PASS
- Acceptance validation: PASS
- no-secrets validation: PASS
- Docker Compose config/build/up/down: PASS in local regression command set
- Service readiness: PASS in local regression command set
- Alembic migration up: PASS in local regression command set
- Demo seed and data validation: PASS in local regression command set
- Backend API validation: PASS in local regression command set
- Connector abstraction validation: PASS in local regression command set
- P0 connector mocked validation: PASS in local regression command set
- Processing pipeline validation: PASS in local regression command set
- Backend pytest suite: PASS in local regression command set
- Frontend build: PASS in local regression command set
- Frontend MVP validation with HTTP smoke: PASS in local regression command set

## Manual / Conditional Coverage

- Real Reddit smoke: NOT_EXECUTED / pending token
- Real Product Hunt smoke: NOT_EXECUTED / pending token
- Real LLM smoke: NOT_EXECUTED / pending token
- Real embedding smoke: NOT_EXECUTED / pending token
- Production deployment validation: NOT_INCLUDED
- Branch protection enforcement: pending_manual_owner_action
- Release tag creation: pending_manual_owner_action

## Coverage Boundary

The MVP acceptance coverage is mock-first and local-first. CI and local final validation do not require real platform credentials or real provider credentials. Manual smoke must be authorized and recorded separately before it can be considered PASS.
