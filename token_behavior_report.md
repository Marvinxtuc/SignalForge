# Subagent Report: Token Behavior Investigation Agent

## 负责范围

Round 0 token behavior investigation for the current external URL. This report verifies cookie behavior, API dependency on cookies, token stripping, and whether `sf_token` appears in backend-visible logs.

This report is NOT_PRODUCTION / DEMO_ONLY / DEPRECATED_FOR_PRODUCTION_DECISION for any production release decision.

## 输入材料

Current external URL, redacted in this report:

```text
https://xhtml-critical-publish-spears.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>
```

Current same-origin API origin:

```text
https://xhtml-critical-publish-spears.trycloudflare.com
```

## 检查文件 / 修改文件

Checked:

- `apps/web/app/api/[...path]/route.ts`
- `apps/web/lib/query.ts`
- `scripts/validate_external_smoke.py`
- Docker logs for `api` and `web`

Modified:

- `token_behavior_report.md`

No source code, runtime config, database migration, or deployment file was modified.

## 执行命令

Actual checks used the complete token in shell variables. The token is redacted in this report.

```bash
python3 scripts/validate_external_smoke.py --url "$SIGNALFORGE_EXTERNAL_SMOKE_URL" --check-api
curl -sS -D headers -o body -w '%{http_code}' -c cookies.txt "$SIGNALFORGE_EXTERNAL_SMOKE_URL"
curl -sS -D headers -o body -w '%{http_code}' -b cookies.txt "https://xhtml-critical-publish-spears.trycloudflare.com/api/projects?page_size=1"
curl -sS -D headers -o body -w '%{http_code}' "https://xhtml-critical-publish-spears.trycloudflare.com/api/projects?page_size=1"
curl -sS -D headers -o body -w '%{http_code}' "https://xhtml-critical-publish-spears.trycloudflare.com/api/projects?page_size=1&sf_token=<invalid_token>"
docker compose -f infra/docker-compose.yml logs --no-color --since 20m api web
rg -n "localStorage|sessionStorage|sf_token" apps/web apps/api scripts --glob '!apps/web/node_modules/**' --glob '!apps/web/.next/**'
```

## 结果证据

External smoke:

```text
PASS: api /api/health returned HTTP 200
PASS: api /api/projects returned HTTP 200
PASS: api /api/settings/platforms returned HTTP 200
PASS: external smoke validation passed for https://xhtml-critical-publish-spears.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>
```

Cookie and API dependency checks:

| Check | HTTP status | Internal Error | Set-Cookie | Result |
| --- | ---: | --- | --- | --- |
| page with real token | 200 | no | no | reachable |
| `/api/health` with CookieJar | 200 | no | no | reachable |
| `/api/projects?page_size=1` with CookieJar | 200 | no | no | reachable |
| `/api/settings/platforms` with CookieJar | 200 | no | no | reachable |
| `/api/health` without cookie | 200 | no | no | reachable |
| `/api/projects?page_size=1` without cookie | 200 | no | no | reachable |
| `/api/settings/platforms` without cookie | 200 | no | no | reachable |
| page with invalid token | 200 | no | no | reachable |
| `/api/projects?page_size=1&sf_token=<invalid_token>` | 200 | no | no | reachable |

Backend-visible log scan:

| Scan | Hits |
| --- | ---: |
| full current token in `api` / `web` logs | 0 |
| invalid token value in `api` / `web` logs | 0 |
| `sf_token` / `sf-token` / `x-sf-token` key in `api` / `web` logs | 0 |
| `Internal Error` in `api` / `web` logs | 0 |
| HTTP 500-like log entries in `api` / `web` logs | 0 |

Static source check:

- No `localStorage` or `sessionStorage` usage was found in `apps/web`, `apps/api`, or `scripts`.
- `sf_token` appears only in expected locations:
  - external smoke redaction logic
  - frontend query allowlist
  - route handler blocked request headers and query stripping
  - frontend validation scripts

## 发现的问题

- Current external access does not appear to depend on cookies.
- The page response did not emit `Set-Cookie`.
- Same-origin API endpoints returned the same successful status with and without CookieJar.
- Passing `sf_token` directly to an API query did not break the API request; route behavior and logs indicate it was not forwarded to FastAPI.
- Invalid token did not block page/API access in the tested current quick tunnel path. This confirms `sf_token` is not functioning as production authentication.

## 阻塞项

- Token behavior is acceptable for external demo smoke, but not acceptable as production authentication.
- Architecture Gate must treat `sf_token` as demo-only and must not rely on it for auth.
- Future cookie/session auth will require an explicit proxy/header strategy; current route handler blocks `cookie` and `authorization`, so this must be revisited before Round 2 auth work.

## 风险

- `sf_token` remains visible in the browser URL by design for this demo flow.
- Quick tunnel access is temporary and does not provide production security guarantees.
- Current API endpoints are publicly reachable through the tunnel without cookie dependency.

## 回滚建议

- Stop the quick tunnel process to revoke external access.
- Do not change proxy authentication forwarding until Architecture Agent consumes this report and defines an explicit strategy.
- Do not promote `sf_token` to production auth.

## 是否通过

PASS_WITH_WARNINGS.

Reason: current token behavior is understood and no token leakage to backend logs was observed, but `sf_token` is demo-only and current API access does not depend on cookie/session auth.
