# Rollback Runbook

Status: PHASE_7_RELEASE_FREEZE_READY
Phase: Phase 7 Testing / Acceptance / Release Freeze

This runbook describes Git-based rollback for the MVP phase commits and release freeze artifacts. Do not use `git reset --hard` unless the owner explicitly approves it.

## General Rules

- Prefer `git revert <commit>` for committed changes.
- Do not delete `.git/`.
- Do not delete project files as a substitute for a reviewed revert.
- If a rollback touches data or migrations, review the phase-specific downgrade or cleanup steps first.
- If a tag exists, remove it only with owner approval.

## Phase -1 Governance Bootstrap

```bash
git revert <phase_-1_commit_hash>
```

Rollback effect: removes governance bootstrap files and early docs-as-code setup.

## Phase 0 Infrastructure

Known commit:

```text
994d157 chore: initialize phase 0 infrastructure
```

Rollback:

```bash
git revert 994d157
```

Rollback effect: removes initial Docker/runtime shell infrastructure. Stop local services first:

```bash
docker compose -f infra/docker-compose.yml down
```

## Phase 1 Data Model

Known commit:

```text
422f1ed feat: add phase 1 data model and migrations
```

Rollback:

```bash
git revert 422f1ed
```

Before or after reverting, if the database contains Phase 1 schema and you need to clean local state:

```bash
docker compose -f infra/docker-compose.yml run --rm api alembic downgrade base
```

The migration downgrade intentionally does not drop the `vector` extension.

## Phase 2 Backend API

Known commit:

```text
df9726b feat: add phase 2 backend api
```

Rollback:

```bash
git revert df9726b
```

Rollback effect: removes backend business API routes, schemas, services, tests, validation, and Phase 2 docs.

## Phase 3 Connector Abstraction

Known commit:

```text
27b610c feat: add phase 3 connector abstraction
```

Rollback:

```bash
git revert 27b610c
```

Rollback effect: removes connector abstraction, mock/disabled connectors, registry/executor integration, tests, and validation script.

## Phase 4 P0 Connectors

Known commit:

```text
09c4fd2 feat: add phase 4 p0 connectors
```

Rollback:

```bash
git revert 09c4fd2
```

Rollback effect: removes Reddit/Product Hunt connector implementation and mocked P0 connector validation. It does not remove real external platform data because CI and default validation do not require real token execution.

## Phase 5 Processing Pipeline

Known commit:

```text
2b76e5f feat: add phase 5 processing pipeline
```

Rollback:

```bash
git revert 2b76e5f
```

Rollback effect: removes processing pipeline, mock LLM/embedding abstractions, clustering/scoring, Signal Quality Gate, processing API, tests, and validation.

## Phase 6 Frontend MVP

Known commit:

```text
83c9537 feat: add phase 6 frontend mvp
```

Rollback:

```bash
git revert 83c9537
```

Rollback effect: removes Frontend MVP pages, frontend API client, frontend validation, docs updates, and the local CORS compatibility fix.

## Phase 7 Release Freeze

Expected commit message:

```text
chore: finalize phase 7 acceptance and release freeze
```

After the Phase 7 commit exists, rollback:

```bash
git revert <phase_7_commit_hash>
```

Rollback effect: removes release freeze docs, release notes, tag checklist updates, final acceptance scripts, and release governance updates.

## Tag Rollback

If the local tag was created with owner approval and must be removed:

```bash
git tag -d v0.1.0-mvp
```

If the tag was pushed remotely, do not delete it without separate owner approval:

```bash
git push origin :refs/tags/v0.1.0-mvp
```

## Docker Cleanup

To stop local runtime services:

```bash
docker compose -f infra/docker-compose.yml down
```

To remove local volumes, request explicit owner approval first because this deletes local database state.
