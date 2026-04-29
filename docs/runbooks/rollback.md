# Rollback Runbook

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

## Phase -1 Rollback

If Phase -1 was committed:

```bash
git revert <commit>
```

If Phase -1 was not committed, remove the Phase -1 files created in this stage.

Do not use `git reset --hard` unless explicitly approved. Deleting `.git/` requires explicit approval because it is a high-risk deletion.

## Later Phase Rollback

Later phases must add concrete commands for infrastructure, migrations, connectors, pipeline, frontend, and release rollback.
