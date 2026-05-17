# Hermes/Codex Approval Protocol

Status: SignalForge repo-local agent protocol.

## Default posture

Repo-local skills are advisory and draft-first. They may inspect the repository and generate
plans, drafts, and patch proposals. They must not write business code, global config, issue
trackers, credentials, hooks, CI, or deployment config without explicit owner approval.

## Pre-change output

Before a write action, output:

- Task judgment
- Current goal
- Confirmed facts
- Risks
- Recommended approach
- Change boundary
- Implementation steps
- Verification standard

## Post-change output

After implementation, output:

- Modified files
- Purpose of changes
- Commands run
- Verification result
- Residual issues
- Rollback method

## Draft-only defaults

- PRDs, issue slices, triage notes, agent briefs, CONTEXT changes, and ADRs are drafts.
- Drafts live under `docs/agents/drafts/` unless explicitly approved otherwise.
- Drafts do not imply issue tracker publication.

## High-risk actions

Require explicit owner approval:

- Global skill installation or sync to `~/.codex/skills`
- `git push`, `git reset`, `git clean`, destructive delete commands
- Issue tracker writes, label changes, comments, or closes
- Production logic changes
- Dependency installation
- Hook, CI, deployment, secret, credential, or permission changes
- Real platform, real LLM, real embedding, or production smoke actions
