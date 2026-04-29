# Architecture Overview

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

This document is a governance skeleton and does not represent final MVP acceptance.

SignalForge is a local-first VOC Radar MVP. P0 is limited to Reddit and Product Hunt. X is P1. Discord is P2.

CI does not depend on real platform tokens. Real platform acceptance is local/manual acceptance. Product Hunt permission limits may be recorded as degraded pass when the connector fails safely and mock data still completes the pipeline.

The MVP must preserve source_url for every signal, provide a Signal Quality Gate, and support a Signal -> Cluster -> Opportunity path.

## Target System

```mermaid
flowchart LR
  Web[Signal Inbox UI] --> API[FastAPI API]
  API --> DB[(PostgreSQL + pgvector)]
  API --> Queue[(Redis)]
  Worker[Celery Worker] --> Reddit[Reddit Connector]
  Worker --> PH[Product Hunt Connector]
  Worker --> Mock[Demo Mock Connector]
  Worker --> LLM[LLM Provider]
  Worker --> DB
```

Phase -1 does not implement these modules. Phase 0 starts infrastructure.
