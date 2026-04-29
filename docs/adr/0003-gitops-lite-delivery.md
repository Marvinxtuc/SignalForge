# ADR 0003: GitOps-lite Delivery

## Context

The project needs traceable, testable, and reversible delivery without production Kubernetes complexity.

## Decision

Use GitOps-lite: Git is the source of truth, PR is the change entry point, CI is the quality gate, and docs/acceptance/rollback assets live in the repo.

## Alternatives

- Heavy GitOps with ArgoCD or Flux: rejected for MVP.
- No governance layer: rejected because the MVP must be auditable.

## Consequences

Phase -1 must create CI, SOP, docs, validation scripts, PR template, CODEOWNERS, and runbooks before business implementation.

## Rollback / Revisit condition

Revisit if the project moves from local-first MVP to production multi-environment deployment.
