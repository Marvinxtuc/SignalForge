---
name: hermes-zoom-out
description: Give a higher-level SignalForge system map for unfamiliar code, modules, callers, data flow, or product behavior. Use when the user asks to zoom out, understand an area, map dependencies, or explain how a local change fits the whole SignalForge system.
---

# Hermes Zoom Out

Use this skill for read-only understanding.

## Required context

Read `docs/agents/domain.md`, then inspect relevant code and docs.

## Output

Provide a concise system map:

- Task judgment
- Current goal
- Confirmed facts
- Relevant modules and callers
- Data flow and domain vocabulary
- Risks or boundaries from ADRs/module docs
- Recommended next step
- Verification standard if later implementation is proposed

Do not modify files.
