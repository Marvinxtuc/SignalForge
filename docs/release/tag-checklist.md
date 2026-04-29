# Tag Checklist

Status: PENDING_MANUAL_OWNER_ACTION
Phase: Phase 7 Testing / Acceptance / Release Freeze

```yaml
tag_status: pending_manual_owner_action
target_tag: v0.1.0-mvp
accepted_commit: 83c9537
accepted_commit_note: Phase 6 validated commit; update to the Phase 7 finalization commit after final validation and commit.
reason: tag creation requires explicit owner approval
push_status: not_pushed
```

## Creation Policy

- Do not create `v0.1.0-mvp` unless the owner explicitly authorizes tag creation.
- Do not push any tag unless the owner separately authorizes remote push.
- Do not treat the missing tag as a release failure while `tag_status` is `pending_manual_owner_action`.

## Preconditions Before Tag Creation

- Phase 7 final acceptance report is complete.
- `validate_final_acceptance.py` passes.
- `validate_release_freeze.py --mode final` passes.
- Full local regression results are recorded in the test report.
- Manual smoke status is recorded honestly as executed or `NOT_EXECUTED / pending token`.
- Git working tree is clean.

## Manual Tag Commands

Only after explicit owner approval:

```bash
git tag -a v0.1.0-mvp -m "SignalForge v0.1.0 MVP"
```

Only after separate explicit owner approval:

```bash
git push origin v0.1.0-mvp
```

## Tag Rollback

If a local tag was created and must be removed:

```bash
git tag -d v0.1.0-mvp
```

If the tag was pushed remotely, remote deletion requires separate owner approval and repository admin review.
