# ADR 0002: P0 Platform Strategy

## Context

The MVP goal is high-value signal density, not platform coverage.

## Decision

P0 includes Reddit and Product Hunt only. X is P1. Discord is P2.

## Alternatives

- Implement all platforms in P0: rejected due to scope risk.
- Use only mock data: rejected because at least two real P0 sources are required for manual acceptance.

## Consequences

Reddit provides deep demand signals. Product Hunt provides structured feedback and competitor validation.

## Rollback / Revisit condition

Revisit if Reddit or Product Hunt access becomes unavailable and mock data is the only viable acceptance path.
