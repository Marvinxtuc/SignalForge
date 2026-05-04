---
name: hermes-write-a-skill
description: Create or update SignalForge repo-local Hermes/Codex skills with approval boundaries, draft-first behavior, and project domain context. Use when adding or revising skills under docs/agents/skills/hermes-codex.
---

# Hermes Write A Skill

Use this skill to create project-local skills only.

## Required context

Read `docs/agents/approval-protocol.md`, `docs/agents/domain.md`, and existing skills under
`docs/agents/skills/hermes-codex/`.

## Skill structure

```text
skill-name/
  SKILL.md
```

Add references or scripts only when they materially reduce repeated work or improve reliability.
Do not add global installation docs, changelogs, or unrelated auxiliary files.

## Required frontmatter

```yaml
---
name: hermes-<capability>
description: <what it does>. Use when <specific SignalForge triggers>.
---
```

## Required behavior

Each skill must:

- Reference `docs/agents/approval-protocol.md`.
- State whether it is read-only, draft-only, or implementation-capable after approval.
- Preserve SignalForge safety boundaries around real platforms, tokens, LLMs, embeddings, CI,
  deployment, and production logic.
- Use concise instructions and progressive disclosure.

## Output

Use the mandatory pre-change and post-change sections from `docs/agents/approval-protocol.md`.

