# Mac Mini Local Production Runbook

Status: DRAFT_FOR_OWNER_ONLY_LOCAL_PRODUCTION

SignalForge Mac mini production is local-only in this phase. Public internet access, tunnels,
Cloudflare, router port forwarding, TLS, multi-user SaaS, billing, X, and Discord remain out of
scope.

## Boundary

- Web binds to `127.0.0.1:3000`.
- API, Postgres, and Redis are Docker-internal only.
- Browser calls API through same-origin Next `/api/*`.
- Owner auth is mandatory when `SIGNALFORGE_REQUIRE_OWNER_AUTH=true`.
- Real platform write and real LLM / embedding calls require run-level approval.

## Secret Setup

Create a local untracked file:

```bash
cp .env.production.example .env.production.local
```

Fill values locally. Do not commit `.env.production.local`.

Required names:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `SIGNALFORGE_OWNER_USERNAME`
- `SIGNALFORGE_OWNER_PASSWORD`
- `SIGNALFORGE_OWNER_SESSION_TOKEN`
- `SIGNALFORGE_OWNER_API_TOKEN`
- `SIGNALFORGE_SESSION_SECRET`

Provider values are optional until real-provider gates are executed.
The real provider flags are also optional and should stay empty until a specific run is approved:

- `SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE`
- `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE`
- `SIGNALFORGE_ALLOW_REAL_LLM_SMOKE`
- `SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE`

## Start

```bash
python3 scripts/validate_mac_local_production.py --strict-env --skip-listener-check
docker compose --env-file .env.production.local -f infra/docker-compose.production.yml up -d
```

## Validate

```bash
python3 scripts/validate_mac_local_production.py --strict-env
```

The validation must show:

- No public or service host port binding in production compose.
- No `cloudflared`, `trycloudflare`, or `ngrok` process.
- No host listener on `8000`, `5432`, or `6379`.
- No secrets validation passes.

## Backup

```bash
python3 scripts/backup_mac_local_production.py
```

Backups are written under `backups/`, which is ignored by git.

## Restore

Restores are destructive and require explicit confirmation:

```bash
python3 scripts/restore_mac_local_production.py \
  --backup-file backups/<backup-file>.dump \
  --confirm-restore
```

## Stop

```bash
docker compose --env-file .env.production.local -f infra/docker-compose.production.yml down
```

Do not remove volumes unless the owner explicitly approves local production data deletion.

## Rollback

- Stop production runtime with `docker compose --env-file .env.production.local -f infra/docker-compose.production.yml down`.
- Revert the production implementation commit with `git revert <commit>`.
- Restore database from the latest verified backup only after owner confirmation.

## Acceptance Markers

- `Mac mini local production: GO` only after auth, lifecycle, provider gate, backup, and local
  production validation pass.
- `Public internet production: NOT_INCLUDED`
- `Tunnel: NOT_STARTED`
- `Product Hunt commercial authorization: PENDING_MANUAL_OWNER_ACTION`
