---
name: hermes-diagnose
description: SignalForge disciplined diagnosis loop for bugs, failing checks, data regressions, connector issues, performance regressions, and signal-quality failures. Use when debugging SignalForge behavior, especially raw_items, signals, embeddings, clusters, opportunities, P0 connectors, processing, reports, or frontend/API failures.
---

# Hermes Diagnose

Use this skill to diagnose SignalForge bugs without guessing.

## Required context

Read `docs/agents/approval-protocol.md` and `docs/agents/domain.md`. Check relevant ADRs and
module-boundary docs before touching implementation.

## Workflow

1. **Build a feedback loop.** Prefer a failing test, validation script, curl/API check, fixture
   replay, or local mocked smoke. For SignalForge, prefer mock-first checks and existing scripts.
2. **Reproduce.** Confirm the loop shows the user's symptom, not a nearby failure.
3. **Hypothesize.** List 3-5 ranked, falsifiable hypotheses with predicted observations.
4. **Instrument narrowly.** Use debugger or targeted logs. If logs are needed, use a unique
   `[DEBUG-...]` prefix and plan cleanup.
5. **Fix plan only unless approved.** A real code fix requires separate owner approval.
6. **Regression test.** Convert the minimized repro into a behavior-level test when a correct
   public seam exists.
7. **Cleanup and post-mortem.** Verify original repro, tests, debug cleanup, and prevention notes.

## SignalForge focus

Prioritize failures in signal calculation, data-source collection, Reddit/Product Hunt mocked
connectors, fallback processing, embeddings, clustering, opportunity scoring, latency, API/web
integration, and Signal Quality Gate behavior.

## Stop condition

If no deterministic or high-reproduction feedback loop can be built, stop and ask for evidence:
logs, payloads, timestamps, fixtures, screenshots, HAR files, or permission for a specific local
instrumentation step. Do not continue with speculation.

## Output

Use the mandatory pre-change and post-change sections from `docs/agents/approval-protocol.md`.
