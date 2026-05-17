---
name: hermes-to-prd
description: Create a SignalForge local Markdown PRD draft from current context. Use when the user wants a PRD for a feature, fix, experiment, connector, processing change, report, frontend workflow, or architecture improvement.
---

# Hermes To PRD

Use this skill to draft, not publish.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/issue-tracker.md`, `docs/agents/domain.md`,
and relevant ADRs/docs.

## Workflow

1. Synthesize from the current conversation and repo context.
2. If core goal, constraints, or acceptance criteria are missing, mark them as open questions.
3. Identify affected modules at a behavior level.
4. Identify test decisions and validation commands.
5. Include explicit out-of-scope and rollback notes.
6. Output a local Markdown PRD draft. Do not publish to GitHub or any issue tracker.

## PRD template

```markdown
# PRD: <title>

## Problem Statement
## Solution
## User Stories
## Implementation Decisions
## Testing Decisions
## Risks
## Out of Scope
## Acceptance Criteria
## Rollback
## Open Questions
```

## Output

Use the mandatory pre-change sections from `docs/agents/approval-protocol.md`.
