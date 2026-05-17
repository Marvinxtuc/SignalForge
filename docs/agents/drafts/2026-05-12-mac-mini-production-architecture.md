# Mac mini Owner-Only Local Production Architecture

Date: 2026-05-12
Status: Architecture draft
Scope: Mac mini owner-only local production, no public ingress

## Task Judgment

SignalForge can proceed to implementation only if the production target remains a local,
owner-only lifecycle on the Mac mini. This architecture gate is decision-complete for that
target and explicitly excludes public ingress, SaaS expansion, and real provider writes without
run-level approval.

## Current Goal

Define the minimum architecture for running SignalForge as a private local production system:

- Owner accesses the Web UI only from the Mac mini or trusted local access path.
- Web and API are protected by production authentication.
- API, Postgres, and Redis are not host-published services.
- Each production run follows an auditable lifecycle from preflight to closeout.
- Real platform writes and real LLM/embedding calls require explicit per-run approval.

## Explicit Boundaries

Included:

- Mac mini local production lifecycle.
- Owner-only browser session.
- Web-to-API access through the Next.js proxy.
- Docker production profile with Web bound to `127.0.0.1`.
- Minimal lifecycle run persistence proposal.
- Redacted logs and rollback metadata for local audit.

NOT_INCLUDED:

- Public internet access.
- Tunnel exposure.
- Cloudflare configuration.
- Router port forwarding.
- Public TLS certificate setup.
- Multi-user authentication.
- SaaS tenancy.
- Billing.
- X connector production integration.
- Discord connector production integration.

TUNNEL_NOT_STARTED:

- No `cloudflared`, `trycloudflare`, ngrok, reverse proxy tunnel, or public URL may be started
  as part of this architecture or its implementation without a separate owner approval.

## Auth And Proxy Design

Production authentication must not rely on `sf_token`.

Required behavior:

- Use an owner-only production session for the Web UI.
- Protect all Web routes that expose production data or production actions.
- Protect all API routes, including read APIs, run lifecycle APIs, collection, processing,
  report generation, settings, exports, and health details beyond a minimal local liveness check.
- Treat `sf_token` as demo-only compatibility behavior, not production authentication.
- In production mode, reject `sf_token` as a sufficient credential for protected operations.
- Store session secrets only in an untracked local environment file.
- Never commit session secrets, provider keys, connector tokens, or local production credentials.

Next proxy requirements:

- Browser calls should continue to use same-origin `/api/*`.
- The Next proxy is the only browser-facing API path.
- The proxy must forward the production auth context to the Docker-internal API safely.
- The proxy must not forward raw demo query tokens as production authority.
- The proxy must strip, normalize, or reject untrusted inbound auth headers from the browser.
- The proxy must redact sensitive query params and headers in logs, including `sf_token`,
  cookies, session IDs, bearer tokens, provider keys, and connector credentials.
- Error responses must not echo secrets, raw upstream headers, or full provider payloads.

Recommended minimum auth model:

- `SIGNALFORGE_PRODUCTION_MODE=true` enables production auth enforcement.
- Web session cookie is `HttpOnly`, `SameSite=Lax` or stricter, and scoped to localhost.
- API accepts a Docker-internal service auth header only from the Next proxy.
- The internal service auth value comes from the same untracked local environment source.
- Direct host access to API is unavailable because API is not host-published.

## Lifecycle State Machine

The production lifecycle is run-based. Each run has one current state and append-only status
events or redacted log lines.

States:

1. `preflight`
2. `collect`
3. `process`
4. `review`
5. `report`
6. `closeout`

Allowed transitions:

- `preflight -> collect` only after local env, auth, storage, no-public-ingress, and secrets
  checks pass.
- `collect -> process` only after source mode and write permissions are recorded.
- `process -> review` only after raw item, signal, embedding, cluster, and opportunity counts are
  recorded, including zero-count explanations.
- `review -> report` only after owner review decision is recorded.
- `report -> closeout` only after report artifact status and rollback notes are recorded.
- Any state may transition to `closeout` with `status=failed` or `status=aborted` if a no-go
  condition appears.

Run-level approvals:

- Real platform read smoke requires explicit run approval.
- Real platform write requires separate explicit run approval.
- Real LLM call requires explicit run approval.
- Real embedding call requires explicit run approval.
- Approval must record approver, timestamp, scope, mode, and expiration or single-run binding.
- Approval must default to denied when missing, stale, ambiguous, or environment-inconsistent.

Modes:

- `mock`: no real platform or model provider calls.
- `preview`: real read or model smoke may run only with explicit approval; no write unless a
  separate write approval exists.
- `production`: owner-approved local production run; still no public ingress and no multi-user
  behavior.

## Minimal Schema Proposal

Implementation should add one minimal table or equivalent persistent store. This is a proposal
only; it does not authorize a migration in this architecture draft.

Recommended table: `production_lifecycle_runs`

Required fields:

| Field | Purpose |
|---|---|
| `id` | Stable run identifier. |
| `created_at` | Run creation timestamp. |
| `updated_at` | Last state/status update timestamp. |
| `closed_at` | Closeout timestamp, nullable until final. |
| `state` | Current lifecycle state. |
| `status` | `pending`, `running`, `passed`, `failed`, or `aborted`. |
| `mode` | `mock`, `preview`, or `production`. |
| `environment` | Local environment label, expected `mac_mini_local`. |
| `owner_session_id_hash` | Non-reversible reference to owner session, not a raw token. |
| `preflight_result` | Structured JSON for auth, env, no-public-ingress, storage, secrets checks. |
| `approval_result` | Structured JSON for real platform write and real LLM/embedding approvals. |
| `source_counts` | Structured JSON for connector/raw item counts. |
| `processing_counts` | Structured JSON for signal/embedding/cluster/opportunity counts. |
| `report_result` | Structured JSON for generated report status and artifact references. |
| `error_code` | Stable failure code, nullable. |
| `error_message_redacted` | Human-readable redacted error summary. |
| `rollback_plan` | Text or JSON rollback steps for the run. |
| `redacted_logs` | Bounded redacted log excerpt or reference. |

Schema constraints:

- Do not store raw secrets, session cookies, bearer tokens, provider keys, or unredacted URLs.
- Do not store full raw provider payloads unless separately approved and redacted.
- Counts and status metadata are preferred over large opaque logs.
- If a separate event table is used later, this run table remains the summary source of truth.

## Production Profile Design

Docker profile requirements:

- Provide a production-local Docker profile distinct from public demo or development exposure.
- Bind Web to `127.0.0.1:<web_port>`.
- Do not publish API to the host.
- Do not publish Postgres to the host.
- Do not publish Redis to the host.
- API is reachable only on the Docker network.
- Postgres and Redis are reachable only on the Docker network.
- Web reaches API through Docker-internal service DNS or an internal base URL.
- Browser reaches API only through same-origin Next `/api/*`.

Secrets and environment:

- Use an untracked local env file, for example `.env.local.production`, for owner session secret,
  internal proxy secret, connector credentials, and provider keys.
- Add no new committed secret values.
- Production profile should fail preflight if required secrets are missing in production mode.
- Production profile should fail preflight if public host bindings are detected for API,
  Postgres, Redis, or tunnel processes.

## No-Go Criteria

Implementation must stop before coding or before run execution if any of these are true:

- Architecture gate is not `PASS`.
- Requested change edits business code, infra, tests, or docs outside the approved scope.
- Public ingress is required to satisfy the requested workflow.
- A tunnel process is running or requested without separate owner approval.
- API, Postgres, or Redis would be host-published.
- Production auth depends on `sf_token`.
- Next proxy forwards raw browser auth headers or tokens without normalization/redaction.
- Secrets would be committed, printed, or stored unredacted.
- Real platform write is possible without run-level approval.
- Real LLM or embedding call is possible without run-level approval.
- Multi-user, SaaS, billing, X, or Discord scope is introduced.
- Rollback path is undefined for lifecycle run records or local runtime changes.

## Verification Gates

Architecture verification:

- Draft explicitly states public internet, tunnel, Cloudflare, router, TLS, multi-user, SaaS,
  billing, X, and Discord are out of scope.
- Draft defines owner-only auth and rejects `sf_token` as production auth.
- Draft defines proxy forwarding and token redaction requirements.
- Draft defines lifecycle states and run-level approvals.
- Draft defines minimal persistent run schema or equivalent.
- Draft defines Docker production-local profile binding and non-published services.

Implementation verification, after separate coding approval:

- Static config check confirms Web is bound to `127.0.0.1`.
- Static config check confirms API/Postgres/Redis have no host-published ports.
- Process check confirms no `cloudflared`, `trycloudflare`, ngrok, or equivalent tunnel.
- Auth smoke confirms unauthenticated Web and API access is rejected.
- Auth smoke confirms authenticated owner session can access Web and same-origin API.
- Proxy smoke confirms sensitive tokens are redacted in logs and responses.
- Lifecycle smoke confirms `preflight -> collect -> process -> review -> report -> closeout`.
- Approval smoke confirms real platform write is blocked without explicit run approval.
- Approval smoke confirms real LLM/embedding calls are blocked without explicit run approval.
- No-secrets validation passes.
- Rollback documentation exists for profile, auth, and lifecycle persistence changes.

## Implementation Decision

Proceed to implementation only after owner approval of this architecture gate. The first
implementation slice should be the smallest verifiable local-production profile and auth gate,
followed by lifecycle persistence and run approval enforcement. Do not implement public ingress,
tunnels, Cloudflare, router changes, TLS, SaaS, billing, X, or Discord in this workstream.

ARCHITECTURE_GATE: PASS
