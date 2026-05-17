---
name: hermes-to-issues
description: Break a SignalForge PRD, plan, or spec into local Markdown vertical-slice issue drafts. Use when converting approved or draft work into independently verifiable slices for agent or human execution.
---

# Hermes To Issues

Use this skill to create issue drafts, not tracker issues.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/issue-tracker.md`, `docs/agents/domain.md`,
and the source PRD/plan.

## Workflow

1. Work from the supplied plan, PRD, or current conversation.
2. Explore code only enough to understand current behavior and boundaries.
3. Break work into vertical tracer-bullet slices.
4. Mark each slice `AFK` or `HITL`.
5. Include dependencies, acceptance criteria, validation command, risk level, rollback, and
   out-of-scope.
6. Ask for approval before writing files.
7. Do not publish to GitHub or modify tracker labels/comments.

## Issue draft template

```markdown
# Issue Draft: <title>

## Type
AFK | HITL

## What to build
## Acceptance Criteria
## Blocked By
## Validation
## Risk
## Rollback
## Out of Scope
```

## Output

Use the mandatory pre-change sections from `docs/agents/approval-protocol.md`.
