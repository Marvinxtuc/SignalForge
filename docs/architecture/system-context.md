# System Context

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

This document is a skeleton and does not represent final MVP acceptance.

## Actors

- Local user: creates research projects and reviews Signal Inbox.
- Reddit API: P0 deep demand source.
- Product Hunt API: P0 structured feedback source.
- LLM provider: classifies signals through JSON output.
- Embedding provider: supports similarity clustering.

## Boundaries

- P0: Reddit + Product Hunt only.
- P1: X.
- P2: Discord.
- CI uses mock/demo data and must not require real platform tokens.
- Real platform acceptance is local/manual acceptance.
- Tag creation may require manual owner action.
