# SignalForge Agent Instructions

## Hermes/Codex local skills

This repo uses repo-local Hermes/Codex skills stored under:

`docs/agents/skills/hermes-codex/`

These skills are also installed globally under `~/.codex/skills/hermes-*` for Codex discovery.
The repo-local copies remain the SignalForge source of truth. Do not resync, overwrite, or remove
global copies unless the owner explicitly approves a separate global-sync step.

Use these skills when the user names them directly or the request matches their trigger:

- `hermes-diagnose` - bugs, failures, regressions, signal/data/connector/debug work.
- `hermes-tdd` - test-first feature or bug work through public behavior.
- `hermes-zoom-out` - system maps and unfamiliar code areas.
- `hermes-grill-with-docs` - plan review, domain language, CONTEXT/ADR proposals.
- `hermes-improve-codebase-architecture` - architecture friction and deep-module candidates.
- `hermes-to-prd` - PRD draft from current context.
- `hermes-to-issues` - local Markdown issue slices from a PRD or plan.
- `hermes-triage` - local Markdown triage notes and agent briefs.
- `hermes-write-a-skill` - create or update SignalForge-local Hermes/Codex skills.

## Mandatory safety protocol

Before any write action, state:

- Task judgment
- Current goal
- Confirmed facts
- Risks
- Recommended approach
- Change boundary
- Implementation steps
- Verification standard

After implementation, report:

- Modified files
- Purpose of changes
- Commands run
- Verification result
- Residual issues
- Rollback method

Default to draft-only for PRDs, issues, triage notes, CONTEXT changes, and ADRs. Drafts live
under `docs/agents/drafts/` unless the user approves another path.

Do not perform these actions without explicit owner approval:

- Global skill installation or sync to `~/.codex/skills`
- `git push`, `git reset`, `git clean`, destructive delete commands
- Issue tracker writes, label changes, comments, or closes
- Production logic changes
- Dependency installation
- Hook, CI, deployment, secret, credential, or permission changes
- Real platform, real LLM, real embedding, or production smoke actions
