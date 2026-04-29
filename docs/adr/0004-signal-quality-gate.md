# ADR 0004: Signal Quality Gate

## Context

SignalForge succeeds only if Signal Inbox surfaces actionable demand signals rather than noise.

## Decision

Use a Signal Quality Gate based on pain_level, signal_confidence_score, is_need_signal, non-noise type, source_url presence, and Signal -> Opportunity traceability.

## Alternatives

- Rank by engagement only: rejected because engagement can amplify noise.
- Accept all LLM output: rejected because JSON failures and model drift must not break jobs.

## Consequences

Processing must include LLM JSON validation, fallback classification, noise filtering, and representative evidence for opportunities.

## Rollback / Revisit condition

Revisit if manual review shows high-value signal density is too low or too many noise items enter top opportunities.
