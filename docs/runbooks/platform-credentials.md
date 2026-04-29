# Platform Credentials Runbook

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

P0 credentials:

- Reddit
- Product Hunt

P1:

- X

P2:

- Discord

CI must not require real platform tokens. Real platform acceptance is local/manual acceptance. `.env` must not be committed. `.env.example` must contain only empty values.

Product Hunt permission limits may be accepted as degraded pass if the connector reports readable status later and mock Product Hunt data completes the pipeline.
