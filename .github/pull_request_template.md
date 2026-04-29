# SignalForge MVP Pull Request Checklist

## Scope

- [ ] This PR does not introduce out-of-phase product functionality.
- [ ] No new database table or migration is included unless explicitly approved.
- [ ] No X or Discord connector is introduced.
- [ ] No auth, billing, multi-user, or production deployment scope is introduced.
- [ ] Real platform or provider smoke is not required for CI.

## Implementation Boundary

- [ ] Data model changes are intentional and documented, or no data model changes are present.
- [ ] Backend API changes are intentional and documented, or no backend changes are present.
- [ ] Connector changes are mock-safe and do not require real tokens in CI.
- [ ] Processing changes use mock/fallback paths in CI.
- [ ] Frontend changes call only the SignalForge backend API.

## Testing

- [ ] `python3 scripts/validate_docs.py`
- [ ] `python3 scripts/validate_acceptance.py`
- [ ] `python3 scripts/validate_no_secrets.py`
- [ ] Backend tests / validation scripts passed where applicable.
- [ ] Frontend build / validation passed where applicable.
- [ ] Docker Compose smoke passed where applicable.

## Security

- [ ] No real token is committed.
- [ ] No `.env` file is tracked.
- [ ] No token is exposed in frontend source, API response, logs, reports, docs, or raw payload.
- [ ] `source_url` evidence remains preserved where applicable.
- [ ] `encrypted_payload` is not rendered in frontend output.

## Release / Acceptance

- [ ] Final acceptance report is updated where applicable.
- [ ] Test report is updated where applicable.
- [ ] Release notes are updated where applicable.
- [ ] Rollback runbook is updated where applicable.
- [ ] Tag checklist is updated where applicable.
- [ ] Manual smoke status is recorded honestly as executed or `NOT_EXECUTED / pending token`.

## Governance

- [ ] `@owner` placeholders are not treated as real owners.
- [ ] Branch protection changes, if needed, are documented for manual owner action.
- [ ] Tag creation is not performed unless explicitly approved.
- [ ] Tag push is not performed unless separately explicitly approved.

## Phase 7 Release Freeze Notes

For `v0.1.0-mvp`, the expected default tag state is:

```yaml
tag_status: pending_manual_owner_action
target_tag: v0.1.0-mvp
reason: tag creation requires explicit owner approval
push_status: not_pushed
```
