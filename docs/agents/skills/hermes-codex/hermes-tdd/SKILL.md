---
name: hermes-tdd
description: SignalForge test-driven development workflow for approved feature or bug work. Use when building or fixing behavior test-first across public interfaces such as API routes, processing services, connector contracts, frontend API clients, signal quality gates, reports, or validation scripts.
---

# Hermes TDD

Use this skill only after the change boundary is approved.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/domain.md`, and relevant testing docs.

## Principles

- Test public behavior, not private implementation.
- Prefer vertical slices: one failing test, minimal implementation, repeat.
- Keep CI mocked. Do not require real platform tokens, real LLM calls, or real embedding calls.
- Do not use TDD as a reason to expand scope or refactor unrelated modules.

## Workflow

1. State the public interface and observable behavior to test.
2. List the exact test command and why it is the narrowest useful feedback loop.
3. Write one failing behavior test only after approval.
4. Implement the smallest change that makes that test pass.
5. Repeat one behavior at a time.
6. Refactor only while green and only inside the approved boundary.
7. Run the narrow test and the relevant validation command before completion.

## SignalForge target behaviors

Prioritize signal calculation, data normalization, Signal Quality Gate decisions, alert/report
generation, connector contracts, fallback processing, API behavior, and frontend API-client
behavior.

## Output

Use the mandatory pre-change and post-change sections from `docs/agents/approval-protocol.md`.

