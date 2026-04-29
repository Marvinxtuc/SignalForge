# ADR 0001: Tech Stack

## Context

SignalForge is a local-first MVP. P0 must prove high-value signal discovery using Reddit and Product Hunt without overbuilding infrastructure.

## Decision

Use FastAPI, Next.js, PostgreSQL with pgvector, Redis, Celery, Docker Compose, and OpenAI-compatible LLM/embedding providers in later phases.

## Alternatives

- Full Kubernetes GitOps: rejected for MVP complexity.
- Single-process app: rejected because connector and processing jobs need queue isolation.

## Consequences

The system stays simple enough for local deployment while keeping a path to async processing and vector clustering.

## Rollback / Revisit condition

Revisit if Docker Compose cannot support local acceptance or if P0 processing requires a different queue model.
