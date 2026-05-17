---
name: hermes-grill-with-docs
description: Stress-test a SignalForge plan against domain language, module boundaries, ADRs, and existing code. Use when reviewing a feature plan, architecture decision, signal-processing change, connector behavior, PRD, or any request that needs terminology and documentation alignment.
---

# Hermes Grill With Docs

Use this skill to clarify intent before implementation.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/domain.md`, relevant ADRs, architecture
docs, and code when the question is answerable from the repo.

## Workflow

1. Explore first when the answer is discoverable from the repo.
2. Ask one material question at a time.
3. For each question, include a recommended answer, basis, risk, and impact.
4. Challenge conflicts with existing SignalForge language, ADRs, phase boundaries, or safety
   constraints.
5. Discuss concrete scenarios: platform credential missing, token redaction, mock-only CI,
   fallback processing, deleted Reddit content, low signal density, report traceability.
6. Produce draft-only documentation proposals.

## Draft outputs

- `CONTEXT.md` changes must be patch proposals only.
- ADRs must be patch proposals only.
- Do not write docs unless separately approved.

## Output

Use the mandatory pre-change sections from `docs/agents/approval-protocol.md`.
