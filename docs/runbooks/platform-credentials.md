# Platform Credentials Runbook

Status: PHASE-1_SKELETON
Phase: Phase -1 Governance Bootstrap

P0 credentials:

- Reddit
- Product Hunt

P1:

- X

P2:

- Discord

CI must not require real platform tokens. Real platform acceptance is local/manual acceptance. `.env` must not be committed. `.env.example` must contain only empty values.

Product Hunt permission limits may be accepted as degraded pass if the connector reports readable status later and mock Product Hunt data completes the pipeline.

## Phase 4 P0 Connector Credentials

Phase 4 uses env-only credential resolution. It does not decrypt or read tokens from `platform_credentials.encrypted_payload`.

Required local environment variables for optional manual smoke:

```bash
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
PRODUCT_HUNT_TOKEN=
```

CI must use mocked Reddit and Product Hunt responses only and must not require real values for these variables.

Manual smoke is disabled unless explicitly enabled:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true
```

Manual smoke does not write `raw_items` unless this second flag is also explicitly enabled:

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true
```

Token safety rules:

- Tokens must only be used in authorization headers.
- Tokens must not be printed to logs.
- Tokens must not be returned by API responses.
- Tokens must not be stored in `raw_payload`.
- Tokens must not be written to docs, reports, or exports.
- `.env` must not be committed.

Reddit rules:

- Use official API/OAuth only.
- Respect `X-Ratelimit-Used`, `X-Ratelimit-Remaining`, and `X-Ratelimit-Reset`.
- Deleted or removed content must not retain deleted body text.
- Missing credentials degrade to disabled.
- Permission limits degrade to `permission_limited`.
- Rate limits degrade to `rate_limited`.

Product Hunt rules:

- Use official GraphQL API only.
- Product Hunt default API use is non-commercial unless Product Hunt grants permission.
- Missing token degrades to disabled.
- Permission or scope limits degrade to `permission_limited`.
- Explicit rate/quota errors degrade to `rate_limited`.

X and Discord credentials remain out of scope until later approved phases.
