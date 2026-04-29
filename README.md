# SignalForge

Status: Phase -1 Governance Bootstrap

SignalForge is a local-first VOC Radar MVP. The MVP goal is to prove that the system can surface high-value, actionable user demand signals, not to maximize collection volume or platform coverage.

## Current Phase

This repository is currently in Phase -1: Governance Bootstrap.

This phase creates the GitOps-lite, Docs-as-Code, and SOP-as-Code governance skeleton only. It does not include business functionality.

Not included in this phase:

- FastAPI application
- Next.js application
- Connector implementation
- Processing Pipeline
- UI pages
- Docker Compose runtime services
- Database models

## Platform Scope

- P0: Reddit and Product Hunt
- P1: X
- P2: Discord

CI must not depend on real platform tokens. Real Reddit and Product Hunt checks are local/manual acceptance items and must be recorded in the final acceptance report later.

## Phase -1 Validation

Run:

```bash
python3 scripts/validate_docs.py
python3 scripts/validate_acceptance.py
python3 scripts/validate_no_secrets.py
```

Do not commit `.env` or real API credentials. `.env.example` must contain only variable names and empty values.

## Next Phase

Phase 0 Infrastructure may start only after Phase -1 is accepted.
