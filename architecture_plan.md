# SignalForge Personal Production v1 Architecture Boundary Review

## Task Judgment

Conclusion: **Architecture Agent PASS with one documented SKIP**.

The inspected source and local evidence support the Personal Production v1 boundary:

- Browser traffic defaults to same-origin `/api/*`.
- Next.js owns the same-origin API proxy.
- Backend service resolution uses server-only `SERVER_API_BASE_URL`.
- Settings exposes status and env-test endpoints only; no credential CRUD endpoint was found.
- UI workflow covers onboarding, settings, collection, processing, signals, opportunities, and reports.
- External smoke remains **SKIPPED**, not failed, because `SIGNALFORGE_EXTERNAL_SMOKE_URL` is unset.

This review does **not** approve production SaaS launch, auto-merge, deployment, data migration, or credential changes.

## Current Goal

Inspect and document the architecture boundary for `/Users/marvin.x/Desktop/SignalForge` without editing source:

1. Same-origin API proxy.
2. Server backend URL.
3. Settings env-only endpoint.
4. No credential CRUD.
5. Personal production UI workflow.
6. Concrete PASS/FAIL evidence.

## Confirmed Facts

- Repository path: `/Users/marvin.x/Desktop/SignalForge`.
- Working tree contains many pre-existing modified/untracked files; this agent did not revert them.
- File ownership for this task: `architecture_plan.md` only.
- Source files were inspected but not edited.
- `infra/docker-compose.yml` sets Web runtime `SERVER_API_BASE_URL: http://api:8000`.
- `apps/web/lib/constants.ts` defaults `DEFAULT_PUBLIC_API_BASE_URL = "/api"` and `DEFAULT_SERVER_API_BASE_URL = "http://api:8000"`.
- `apps/web/app/api/[...path]/route.ts` is the Next API proxy and declares `runtime = "nodejs"`.
- Backend `GET /health` exists in `apps/api/app/main.py`.
- Backend Settings route surface is:
  - `GET /api/settings/platforms`
  - `GET /api/settings/credentials/status`
  - `POST /api/settings/platforms/{platform}/test`
- Settings schemas return credential status metadata only; no secret payload field is included in `CredentialStatusItem`.
- `apps/api/tests/test_settings_api.py` asserts `encrypted_payload`, `token`, and bearer material are not returned by Settings status/env-test responses.
- `apps/web/e2e/personal-workflow.spec.ts` covers the personal production UI workflow and asserts no `encrypted_payload`, `PRODUCT_HUNT_TOKEN`, or `REDDIT_CLIENT_SECRET` text appears.

## Architecture Boundary Checklist

| Boundary item | Result | Concrete evidence |
| --- | --- | --- |
| Browser API base does not depend on `localhost:8000` | PASS | `apps/web/lib/constants.ts:5-10` defaults public base to `/api`; `rg` found no `localhost:8000` in `apps/web`; Docker compose does not set `NEXT_PUBLIC_API_BASE_URL`. |
| Same-origin `/api/*` proxy exists | PASS | `apps/web/app/api/[...path]/route.ts:29-55` exports HTTP methods and routes all methods into `proxyBackendRequest`. |
| Proxy uses server-only backend URL | PASS | `apps/web/app/api/[...path]/route.ts:1` imports `SERVER_API_BASE_URL`; `route.ts:99` constructs upstream URL from it; `infra/docker-compose.yml:23` sets it to `http://api:8000`. |
| `/api/health` maps to backend `/health` | PASS | `apps/web/lib/api.ts:150-153` maps browser `/health` to `/api/health`; `route.ts:98` maps proxy path `health` to upstream `/health`; `apps/api/app/main.py:44-50` defines backend `GET /health`. |
| Absolute backend paths are rejected by client | PASS | `apps/web/lib/api.ts:108-115` rejects `http(s)://` paths with `invalid_backend_path`. |
| Proxy strips credential-bearing browser inputs | PASS | `apps/web/app/api/[...path]/route.ts:10-25` blocks authorization/cookie/token headers; `route.ts:101-104` strips `sf_token` from upstream query params. |
| Settings env-only endpoint exists | PASS | `apps/api/app/api/routes/settings.py:24-29` exposes `POST /api/settings/platforms/{platform}/test`; `apps/api/app/services/settings.py:84-126` reads required env names from process/env mapping and returns `missing_env` or `configured_unverified` without live credential verification. |
| No credential CRUD in Settings API | PASS | `apps/api/app/api/routes/settings.py:14-29` has only two GET endpoints and one env-test POST; no create/update/delete credential endpoint was found by `rg` over API routes/services/schemas/web client. |
| Settings status excludes secret payload | PASS | `apps/api/app/schemas/settings.py:37-45` includes `platform`, `status`, `credential_name`, `last_checked_at`; `apps/api/tests/test_settings_api.py:24-34` asserts no `encrypted_payload` or `token`. |
| UI Settings workflow is credential-safe | PASS | `apps/web/components/settings/SettingsPage.tsx:42-49` loads platform/status APIs; `SettingsPage.tsx:87-93` calls env-test; `SettingsPage.tsx:107-109` and `124-135` state status-only/no credential CRUD; `SettingsPage.tsx:273-274` sanitizes env-token-like markers. |
| Personal production UI workflow exists | PASS | `apps/web/e2e/personal-workflow.spec.ts:11-55` covers onboarding, settings test, collection logs, dashboard processing, signal feedback, opportunities, and report export. |
| Docker compose config validates | PASS | `docker compose -f infra/docker-compose.yml config` exited 0 and rendered `web.environment.SERVER_API_BASE_URL: http://api:8000`. |
| Frontend MVP validator passes | PASS | `python3 scripts/validate_frontend_mvp.py` exited 0 with `PASS: API client is limited to the SignalForge backend boundary` and `PASS: frontend MVP validation succeeded`. |
| Docker web build | PASS, supplied evidence | Requester-provided local evidence: `docker web build exit 0`. This agent did not rerun the build. |
| Playwright workflow | PASS, supplied evidence | Requester-provided local evidence: `Playwright PASS`. This agent inspected the E2E workflow spec but did not rerun Playwright. |
| External smoke | SKIP | Requester-provided local evidence: skipped due missing `SIGNALFORGE_EXTERNAL_SMOKE_URL`; this agent confirmed `SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set`. |

## Risk Points

- `NEXT_PUBLIC_API_BASE_URL` remains an optional override. Risk is controlled only if deployment/tunnel environments leave it unset or set it to a same-origin relative path.
- External smoke is not executed without `SIGNALFORGE_EXTERNAL_SMOKE_URL`; external tunnel behavior is therefore not proven in this run.
- Docker web build and Playwright PASS are accepted as requester-supplied local evidence here, not re-executed by this agent.
- The current working tree is dirty; this report does not attribute or validate unrelated edits.
- Settings `credential_name` is non-secret metadata by schema, but owners should avoid placing secret material in credential names.

## Recommended Plan

Keep the architecture as-is for Personal Production v1:

1. Continue browser calls through the centralized API client.
2. Continue defaulting browser API base to same-origin `/api`.
3. Keep Docker Web runtime on `SERVER_API_BASE_URL=http://api:8000`.
4. Keep Settings credential-safe: status and env-test only, no CRUD.
5. Before external release approval, run external smoke with `SIGNALFORGE_EXTERNAL_SMOKE_URL` set.

## Change Boundary

- Modified: `architecture_plan.md`.
- Inspected: source, tests, Docker files, docs references listed in this report.
- Not modified: app source, tests, package files, Docker files, env files, scripts, data, secrets, or deployment config.

## Implementation Steps

1. Read repository file list and current git status.
2. Read `architecture_plan.md` before editing.
3. Inspected Next API proxy, API client, constants, Settings UI, Settings backend route/service/schema, FastAPI main, Docker compose, Dockerfiles, and E2E workflow spec.
4. Searched for API base, Settings, credential, token, and CRUD references.
5. Ran lightweight validation commands.
6. Updated only this report with concrete evidence and PASS/SKIP status.

## Validation Standard

Architecture boundary is accepted for Personal Production v1 when:

- Browser default API base is same-origin `/api`.
- Browser code does not require `localhost:8000`.
- Next proxy maps `/api/*` to backend `/api/*` and `/api/health` to backend `/health`.
- Backend URL is server runtime configuration only.
- Settings exposes env/status checks without credential CRUD.
- UI workflow passes validator/Playwright evidence.
- External smoke is either passed with URL evidence or explicitly marked SKIP.

## Commands Executed

| Command | Exit | Stdout/stderr summary |
| --- | ---: | --- |
| `pwd && rg --files` | 0 | Listed repository root and files. |
| `git status --short` | 0 | Showed dirty working tree with many modified/untracked files. |
| `test -f architecture_plan.md && sed -n '1,260p' architecture_plan.md` | 0 | Read existing placeholder architecture report. |
| `nl -ba 'apps/web/app/api/[...path]/route.ts' \| sed -n '1,260p'` | 0 | Confirmed Next same-origin proxy implementation. |
| `nl -ba apps/web/lib/api.ts \| sed -n '1,560p'` | 0 | Confirmed API URL resolution, `/api/health`, Settings client endpoints. |
| `nl -ba apps/web/lib/constants.ts \| sed -n '1,220p'` | 0 | Confirmed `/api` public default and `http://api:8000` server default. |
| `nl -ba apps/web/components/settings/SettingsPage.tsx \| sed -n '1,280p'` | 0 | Confirmed status-only Settings UI and env test action. |
| `nl -ba apps/api/app/api/routes/settings.py \| sed -n '1,260p'` | 0 | Confirmed Settings route surface. |
| `nl -ba apps/api/app/services/settings.py \| sed -n '1,320p'` | 0 | Confirmed env-only platform test behavior. |
| `nl -ba apps/api/app/schemas/settings.py \| sed -n '1,260p'` | 0 | Confirmed credential status schema excludes secret payload. |
| `rg -n "settings\|credential\|credentials\|Credential\|PlatformCredential\|sf_token\|SERVER_API_BASE_URL\|NEXT_PUBLIC_API_BASE_URL\|/api/settings\|/api/health\|fetch\\(" ...` | 0 | Confirmed relevant references and no browser `localhost:8000` dependency in app source. |
| `nl -ba apps/api/app/main.py ... && nl -ba infra/docker-compose.yml ...` | 0 | Confirmed backend health endpoint and compose backend URL. |
| `nl -ba apps/api/tests/test_settings_api.py \| sed -n '1,320p'` | 0 | Confirmed tests for no token/secret payload in Settings responses. |
| `nl -ba apps/web/e2e/personal-workflow.spec.ts \| sed -n '1,260p'` | 0 | Confirmed personal production workflow test. |
| `rg -n "@(router\|app)\\.(post\|put\|patch\|delete)\\(...` | 0 | Confirmed Settings has no credential CRUD route; other CRUD routes are unrelated domain APIs. |
| `nl -ba apps/web/Dockerfile ... && nl -ba apps/api/Dockerfile ...` | 0 | Confirmed Web standalone runtime and API runtime Docker commands. |
| `for f in apps/web/app/...; do sed -n '1,80p' "$f"; done` | 0 | Confirmed UI routes for onboarding, signals, dashboard, opportunities, logs, reports, settings. |
| `docker compose -f infra/docker-compose.yml config` | 0 | Rendered compose config with Web `SERVER_API_BASE_URL: http://api:8000`. |
| `python3 scripts/validate_frontend_mvp.py` | 0 | PASS, including backend boundary and optional frontend HTTP smoke. |
| `if [ -z "${SIGNALFORGE_EXTERNAL_SMOKE_URL:-}" ]; then echo "SKIP..." ...` | 0 | Printed `SKIP: SIGNALFORGE_EXTERNAL_SMOKE_URL is not set`. |
| `rg -n "localhost:8000\|127\\.0\\.0\\.1:8000\|NEXT_PUBLIC_API_BASE_URL..." ...` | 0 | Confirmed public default `/api`; only `.env.example` mentions empty `NEXT_PUBLIC_API_BASE_URL`. |
| `rg -n "settings\|credentials\|platforms/.*/test..." ...` | 0 | Confirmed Settings route/client/test evidence. |
| `git diff -- architecture_plan.md \| sed -n '1,260p'` | 0 | Inspected prior diff before replacing placeholder report. |
| `nl -ba apps/web/app/api/[...path]/route.ts \| sed -n '1,240p'` | 1 | Harmless failed read: zsh expanded unquoted brackets; rerun quoted succeeded. |
| `nl -ba apps/web/app/page.tsx ... apps/web/app/settings/page.tsx \| sed -n '1,260p'` | 1 | Harmless failed read: `nl` usage with combined file list; rerun via loop succeeded. |
| `python3 scripts/validate_external_smoke.py` | 2 | Expected CLI usage error because `--url` is required; env-gated SKIP command above records the intended skip state. |

## Validation Results

- Overall architecture boundary: **PASS**.
- Same-origin API proxy: **PASS**.
- Server backend URL: **PASS**.
- Settings env-only endpoint: **PASS**.
- No credential CRUD: **PASS**.
- UI workflow evidence: **PASS** from supplied Playwright evidence and inspected E2E workflow; frontend MVP validator PASS was re-run.
- External smoke: **SKIP**, because `SIGNALFORGE_EXTERNAL_SMOKE_URL` is missing.

## Residual Issues

- External smoke needs a real external URL before it can be marked PASS.
- Docker web build and Playwright were not re-run by this agent; they remain requester-supplied evidence for this report.
- Dirty working tree remains outside this report's ownership.

## Rollback

This task modified only `architecture_plan.md`.

```bash
git restore -- architecture_plan.md
```

No service, migration, secret, or deployment rollback is required because no source, data, config, or credential files were changed.
