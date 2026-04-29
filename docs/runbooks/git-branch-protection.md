# Git Branch Protection Runbook

Status: PENDING_MANUAL_OWNER_ACTION
Phase: Phase 7 Testing / Acceptance / Release Freeze

This runbook records the recommended GitHub branch protection policy for SignalForge. Codex must not configure branch protection automatically unless the owner explicitly grants GitHub admin authorization.

## Owner Placeholder

`@owner` must be replaced with the actual GitHub username or team before enforcement.

@owner must be replaced by the actual GitHub username or team before branch protection is enforced.

Current status:

```yaml
owner_placeholder: "@owner"
owner_replacement_status: pending_manual_owner_action
branch_protection_status: pending_manual_owner_action
```

## Recommended Protected Branches

- `main`
- Release branches, if introduced later.

## Required Rules

- Require pull request before merging.
- Require status checks to pass before merging.
- Require conversation resolution before merging.
- Require linear history.
- Disallow force pushes.
- Disallow branch deletion.
- Require CODEOWNERS review after `@owner` is replaced.
- Restrict bypass permissions to the repository owner/admin group.

## Recommended Required Checks

- `ci-docs`
- `ci-code`
- `ci-docker`
- `ci-data`
- `ci-acceptance`

`ci-acceptance` is mock-only release readiness and must not require real platform tokens, real provider tokens, tag creation, or tag push.

## Manual Configuration Steps

1. Replace `@owner` with the actual GitHub user or team.
2. Confirm required checks are green on the target branch.
3. Configure branch protection in GitHub repository settings.
4. Confirm force-push and deletion protections are enabled.
5. Confirm CODEOWNERS review is enforced only after CODEOWNERS points to a real owner.
6. Record the configuration date and operator in the final acceptance report.

## Explicit Non-Goals

- Codex does not configure branch protection in Phase 7.
- Codex does not push branches or tags in Phase 7.
- Codex does not create production deployment rules in Phase 7.
