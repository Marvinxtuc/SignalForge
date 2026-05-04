---
name: hermes-triage
description: Triage SignalForge bugs, enhancements, PRDs, and issue drafts through local Markdown notes and agent briefs. Use when reviewing incoming work, deciding readiness, preparing AFK agent briefs, or classifying SignalForge tasks.
---

# Hermes Triage

Use this skill for local triage drafts only.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/issue-tracker.md`,
`docs/agents/triage-labels.md`, and `docs/agents/domain.md`.

## Workflow

1. Gather issue/plan context and prior notes.
2. Classify one category role: `bug` or `enhancement`.
3. Classify one state role: `needs-triage`, `needs-info`, `ready-for-agent`,
   `ready-for-human`, or `wontfix`.
4. For bugs, attempt local/mock reproduction before recommending readiness.
5. Surface relevant module-boundary, ADR, safety, credential, and phase constraints.
6. Draft triage notes or an agent brief. Do not post comments, apply labels, or close external
   issues.

## Agent brief template

```markdown
# Agent Brief: <title>

## Category
bug | enhancement

## State
needs-triage | needs-info | ready-for-agent | ready-for-human | wontfix

## Current Behavior
## Desired Behavior
## Key Interfaces
## Acceptance Criteria
## Validation
## Risks
## Out of Scope
```

## Output

Use the mandatory pre-change sections from `docs/agents/approval-protocol.md`.

