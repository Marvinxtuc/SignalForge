---
name: hermes-improve-codebase-architecture
description: Find SignalForge architecture friction, deep-module opportunities, testability gaps, and AI-navigability improvements. Use when reviewing module boundaries, reducing coupling, improving seams, or preparing a refactor proposal.
---

# Hermes Improve Codebase Architecture

Use this skill for architecture review and candidate discovery, not immediate refactoring.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/domain.md`, `docs/architecture/`, and
relevant ADRs before inspecting code.

## Vocabulary

- Module: anything with an interface and implementation.
- Interface: everything callers must know to use a module.
- Implementation: the code inside.
- Seam: where behavior can be altered without editing callers in place.
- Adapter: a concrete implementation at a seam.
- Depth: high leverage behind a small interface.
- Locality: change and bugs concentrated in one place.

## Workflow

1. Explore the area and note real friction, not theoretical style preferences.
2. Separate confirmed facts from architectural judgment.
3. Apply the deletion test to suspected shallow modules.
4. Present numbered deepening candidates only.
5. For each candidate include files/modules, problem, solution, benefits, risks, validation, and
   rollback.
6. Do not design final interfaces or refactor until the owner picks a candidate and approves the
   next step.

## Output

Use the mandatory pre-change sections from `docs/agents/approval-protocol.md`.
