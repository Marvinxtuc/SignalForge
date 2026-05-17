# SignalForge Runtime Plan

## Status

PASS

## Task Judgment

Round 1 scope is limited to Docker Compose runtime environment wiring and runtime documentation. Application source code is out of scope for this pass.

## Current Goal

- Run `web` with server-side access to the API through Docker Compose service DNS: `http://api:8000`.
- Avoid exposing or baking `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` into the web container runtime.
- Allow the API to accept browser-origin requests from the local web origins when direct browser calls exist.

## Confirmed Facts

- `apps/web/next.config.mjs` sets `output: "standalone"`.
- `apps/web/Dockerfile` copies `.next/standalone` into the runner image and starts the app with `node server.js`.
- `infra/docker-compose.yml` defines `api` and `web` in the same Compose project network, so `web` can resolve the API service by the Compose DNS name `api`.
- `infra/docker-compose.yml` now renders `web.environment.SERVER_API_BASE_URL=http://api:8000`.
- Rendered Compose config does not contain `web.environment.NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`.
- `apps/web/app/api/[...path]/route.ts` exists and imports `SERVER_API_BASE_URL` for the web-to-api proxy path.
- `apps/web/lib/constants.ts` still supports `NEXT_PUBLIC_API_BASE_URL` as an optional override, but the default public base URL is `/api`, not `http://localhost:8000`.

## Runtime Environment Design

### Web to API inside Compose

`web` receives:

```env
SERVER_API_BASE_URL=http://api:8000
```

Inside Docker Compose, `api` is the service hostname. Server-side code running in the `web` container can call `http://api:8000` without going through the host machine or a public tunnel.

### Standalone Next.js Runtime Env

With `output: "standalone"` and `CMD ["node", "server.js"]`, Next.js server runtime code reads `process.env` from the running container process. Route handlers, server components, and other server-only modules can therefore observe runtime variables such as `SERVER_API_BASE_URL` when the container starts.

This is distinct from `NEXT_PUBLIC_*` variables, which are intended for browser-exposed configuration and can be inlined into client bundles at build time. For the desired architecture, route handlers should proxy browser requests to the API using `SERVER_API_BASE_URL`, keeping the browser from needing direct access to `api:8000`.

Runtime note: `SERVER_API_BASE_URL` is read by the Node process started by `node server.js`. Changing the value requires restarting the `web` container process.

### Browser Access Model

The browser should access the web app at:

```text
http://localhost:3000
```

The browser does not need to directly call:

```text
http://api:8000
```

`api` is a Docker-internal hostname and is not expected to resolve from the host browser. The intended flow is:

```text
Browser -> web on localhost:3000 -> Next.js server runtime/route handler -> api on http://api:8000
```

### API CORS

`api` receives:

```env
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

This allows local browser origins if any current or transitional code path still calls the API directly from the browser.

### External Tunnel Configuration

For an external tunnel, expose the `web` service, not the internal `api` service:

```text
Public tunnel URL -> host localhost:3000 -> web container
```

Recommended configuration:

- Keep `SERVER_API_BASE_URL=http://api:8000` inside Compose.
- Add the public tunnel web origin to API CORS only if browser-origin API calls are still present.
- Do not configure browser code with `http://api:8000`; that hostname is only valid inside the Compose network.
- If direct public API access is intentionally required, expose the API through a separate controlled tunnel or reverse proxy and add that public origin explicitly to `CORS_ALLOW_ORIGINS`.

## Change Boundary

Changed files:

- `infra/docker-compose.yml`
- `runtime_plan.md`

Reviewed but unchanged:

- `apps/web/Dockerfile`

No database files, deployment configuration, or application source code were changed in this pass.

## Implementation Steps

1. Set `api.environment.CORS_ALLOW_ORIGINS`.
2. Replace `web.environment.NEXT_PUBLIC_API_BASE_URL` with `web.environment.SERVER_API_BASE_URL`.
3. Document the standalone runtime model, Compose DNS behavior, browser access model, and tunnel guidance.

## Verification Standard

- `docker compose -f infra/docker-compose.yml config` renders `SERVER_API_BASE_URL: http://api:8000` under `web`.
- Rendered Compose config does not contain `NEXT_PUBLIC_API_BASE_URL: http://localhost:8000`.
- Rendered Compose config contains `CORS_ALLOW_ORIGINS: http://localhost:3000,http://127.0.0.1:3000` under `api`.
- Runtime documentation records that the standalone Next.js server process can read `SERVER_API_BASE_URL` from the runtime container environment.

## Verification Result

Commands executed:

```sh
git status --short -- infra/docker-compose.yml apps/web/Dockerfile runtime_plan.md blocking_issue.md
git diff -- infra/docker-compose.yml apps/web/Dockerfile
rg -n "NEXT_PUBLIC_API_BASE_URL|SERVER_API_BASE_URL|localhost:8000|api:8000" infra/docker-compose.yml apps/web/Dockerfile apps/web runtime_plan.md
docker compose -f infra/docker-compose.yml config
sed -n '1,120p' apps/web/next.config.mjs
sed -n '1,180p' apps/web/lib/constants.ts
sed -n '1,200p' 'apps/web/app/api/[...path]/route.ts'
```

Results:

- PASS: Compose rendered `web.environment.SERVER_API_BASE_URL: http://api:8000`.
- PASS: Compose rendered no `NEXT_PUBLIC_API_BASE_URL: http://localhost:8000`.
- PASS: Compose rendered `api.environment.CORS_ALLOW_ORIGINS: http://localhost:3000,http://127.0.0.1:3000`.
- PASS: Dockerfile uses standalone output and starts `node server.js`, so server runtime env is read from the running container process.
- PASS: No `blocking_issue.md` was required.

## Residual Issues

- `NEXT_PUBLIC_API_BASE_URL` remains present in `apps/web/lib/constants.ts` as an optional override. This is not a Compose runtime blocker because Compose no longer sets it to `http://localhost:8000`, and the default browser path is `/api`.
- No container build or runtime smoke test was executed in this pass; verification was limited to static file review and `docker compose config`.

## Rollback

Revert only this Round 1 runtime change by restoring:

- `api.environment.CORS_ALLOW_ORIGINS` removal if no longer desired.
- `web.environment.NEXT_PUBLIC_API_BASE_URL: http://localhost:8000` if returning to browser-direct localhost API calls.
- Remove `runtime_plan.md` only with explicit approval, because file deletion requires approval.
