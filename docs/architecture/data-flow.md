# Data Flow

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

This document is a skeleton and does not represent final MVP acceptance.

## MVP Flow

```mermaid
flowchart TD
  A[Project Keywords] --> B[Reddit/Product Hunt/Mock Connectors]
  B --> C[raw_items]
  C --> D[Clean Redact Dedupe]
  D --> E[LLM JSON Classification]
  E --> F[Fallback if needed]
  F --> G[signals]
  G --> H[clusters]
  H --> I[opportunities]
  I --> J[Signal Inbox and Opportunity Board]
```

All signals must preserve source_url. Product Hunt permission limits can degrade safely if logs are readable and mock Product Hunt data still completes the flow.
