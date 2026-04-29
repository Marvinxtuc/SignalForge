# External Smoke Report

Status: PASS

## Task Judgment

- Local `localhost:3000` was available and provided a valid smoke target.
- A user-approved temporary Cloudflare quick tunnel was created for real external validation.
- The first generated tunnel returned TLS EOF and was discarded; the second generated tunnel passed page and same-origin API smoke.
- No `blocking_issue.md` was created.

## Modified Files

- `scripts/validate_external_smoke.py`
- `external_smoke_report.md`

## Change Purpose

- Keep the external smoke script runnable with Python standard library only.
- Ensure the script supports `--url` and `--check-api`.
- Validate the page response is reachable, does not return HTTP 500, and does not contain `Internal Error`.
- Validate same-origin API smoke endpoints when `--check-api` is set:
  - `/api/health`
  - `/api/projects?page_size=1`
  - `/api/settings/platforms`
- Redact `sf_token` values from all script output, including PASS and FAIL paths.

## Executed Commands

```bash
python3 scripts/validate_external_smoke.py --help
python3 -m py_compile scripts/validate_external_smoke.py
python3 scripts/validate_external_smoke.py --url 'http://localhost:3000/signals?projectId=local-smoke&sf_token=<redacted>' --check-api
python3 scripts/validate_external_smoke.py --url 'http://localhost:9/signals?sf_token=<redacted>'
cloudflared tunnel --url http://localhost:3000
python3 scripts/validate_external_smoke.py --url 'https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>' --check-api
rg -n '<synthetic-redaction-token>' scripts/validate_external_smoke.py external_smoke_report.md || true
```

## Validation Result

Local smoke target:

```text
http://localhost:3000/signals?projectId=local-smoke&sf_token=<redacted>
```

Script output:

```text
PASS: api /api/health returned HTTP 200
PASS: api /api/projects returned HTTP 200
PASS: api /api/settings/platforms returned HTTP 200
PASS: external smoke validation passed for http://localhost:3000/signals?projectId=local-smoke&sf_token=<redacted>
```

Confirmed:

- `--url` is present and required.
- `--check-api` is present and enables same-origin API checks.
- `/signals` returned a reachable page and included a required UI marker.
- `/api/health` returned HTTP 200.
- `/api/projects?page_size=1` returned HTTP 200.
- `/api/settings/platforms` returned HTTP 200.
- No HTTP 500 was observed in the validated page or API endpoints.
- No `Internal Error` marker was observed by the validation script.
- Failure-path output redacts `sf_token`.
- Search found no stored synthetic redaction token value in the script or report.

Real external smoke target:

```text
https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>
```

Real external script output:

```text
PASS: api /api/health returned HTTP 200
PASS: api /api/projects returned HTTP 200
PASS: api /api/settings/platforms returned HTTP 200
PASS: external smoke validation passed for https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>
```

Log scan:

- Web/API logs contained no `500`, `Internal Error`, full smoke token, `sf_token=`, `localhost:8000`, or `127.0.0.1:8000` matches.
- Temporary Cloudflare tunnel was stopped after validation.

## Residual Issues

- External tunnel validation passed with a temporary user-approved Cloudflare quick tunnel.
- The script does not create or manage tunnels by design.
- `python3 -m py_compile` generated `scripts/__pycache__/validate_external_smoke.cpython-314.pyc` during validation. Cleanup requires user approval because deleting files is approval-gated.

## Rollback

```bash
git restore --staged scripts/validate_external_smoke.py external_smoke_report.md
rm -f scripts/validate_external_smoke.py external_smoke_report.md
```

Rollback note: both files are currently untracked in this workspace. Use the commands only if discarding this round's external smoke artifacts is approved.
