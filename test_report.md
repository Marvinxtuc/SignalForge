# SignalForge Round 1 Test Report

## 任务判断

结论：Round 1 测试结论为 PASS，可进入 Go/No-Go 汇总。

依据：`qa_test_report.md`、`external_smoke_report.md`、`security_review.md` 均给出 PASS；Backend 最终验证 PASS；Frontend 验证项通过；Runtime 配置计划与 Docker Compose 目标一致。

## 当前目标

- 汇总 Round 1 必需验证结果。
- 明确测试覆盖、命令证据、残留风险和回滚方式。
- 为 `go_no_go_decision.md` 提供可复核依据。

## 已确认事实

- QA Final Verification：PASS。
- External Smoke：PASS。
- Security Final Verification：PASS。
- Backend Final Verification：PASS。
- Frontend Change Report：前端 validator、TypeScript 检查、临时 Next dev server smoke 均通过。
- Runtime Plan：明确 Web 使用 `SERVER_API_BASE_URL=http://api:8000`，不再依赖浏览器公开 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`。
- `git status --short` 显示当前存在应用代码、脚本与报告文件的未提交变更；本发布管理步骤未执行 git 暂存、提交、重置或回滚。

## 测试结果汇总

| 验证项 | 来源 | 结果 |
| --- | --- | --- |
| API Docker pytest | 主控复跑 / `qa_test_report.md` | PASS，`123 passed in 2.76s` |
| Web production build | `qa_test_report.md` | PASS |
| Same-origin `/api/health` | `qa_test_report.md` | PASS，HTTP 200 |
| Same-origin `/api/projects?page_size=1` | `qa_test_report.md` | PASS，HTTP 200 |
| Same-origin `/api/settings/platforms` | `qa_test_report.md` | PASS，HTTP 200 |
| Frontend MVP validator | `qa_test_report.md` | PASS |
| No-secrets validation | `qa_test_report.md` / `security_review.md` | PASS |
| Browser bundle localhost guard | `qa_test_report.md` | PASS，running web container bundle no `http://localhost:8000` matches |
| Platform select includes `product_hunt` | `qa_test_report.md` | PASS |
| External `/signals` page smoke | 主控真实 Cloudflare tunnel / `external_smoke_report.md` | PASS |
| External same-origin API smoke | 主控真实 Cloudflare tunnel / `external_smoke_report.md` | PASS |
| Proxy token stripping review | `security_review.md` | PASS |
| CORS config tests | `backend_change_report.md` | PASS，`3 passed in 0.36s` |

## 执行命令

已纳入子报告记录的关键命令：

```bash
docker compose -f infra/docker-compose.yml build
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm web npm run build
curl -i http://localhost:3000/api/health
curl -i 'http://localhost:3000/api/projects?page_size=1'
curl -i http://localhost:3000/api/settings/platforms
python3 scripts/validate_no_secrets.py
python3 scripts/validate_frontend_mvp.py --require-http
python3 scripts/validate_external_smoke.py --url 'https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>' --check-api
docker compose -f infra/docker-compose.yml exec -T web sh -lc "grep -R -n 'http://localhost:8000' .next/static .next/server 2>/dev/null || true"
docker compose -f infra/docker-compose.yml run --rm api pytest tests/test_cors_config.py
```

本 Release Manager 步骤执行的读取命令：

```bash
git status --short
sed -n '1,220p' implementation_plan.md
sed -n '1,260p' architecture_plan.md
sed -n '1,260p' backend_change_report.md
sed -n '1,260p' frontend_change_report.md
sed -n '1,280p' runtime_plan.md
sed -n '1,280p' security_review.md
sed -n '1,280p' qa_test_report.md
sed -n '1,280p' external_smoke_report.md
sed -n '1,260p' scripts/validate_external_smoke.py
```

## 风险点

- `sf_token` 是临时 demo query/cookie 访问控制方案，会出现在浏览器 URL、历史记录、截图或外部日志中；不适合作为长期认证方案。
- Docker Compose 构建过程中存在 buildx 插件 warning，但未阻断构建或测试。
- 本地 `apps/web/.next` 存在 stale cache artifact；QA 确认 running web container bundle 不包含 `http://localhost:8000`。

## 验证标准

- QA、External Smoke、Security 必须 PASS。
- 浏览器侧业务 API 必须走同源 `/api/*`。
- running web container bundle 不得包含浏览器直连 `http://localhost:8000` 的证据。
- `sf_token` 不得完整写入报告，不得转发至 FastAPI。
- 不得新增 migration，不得调用真实外部平台 API。

## 验证结果

PASS。

## 残留问题

- 无 Go-blocking 测试残留问题。
- `sf_token` demo 风险保留为已知非阻断风险。
- `scripts/__pycache__/validate_external_smoke.cpython-314.pyc` 是验证过程中生成的缓存文件；删除需要另行批准。

## 回滚方式

- 本文件为发布管理报告；回滚时恢复或删除 `test_report.md` 即可。
- 应用变更回滚以各 subagent 报告中的文件清单为准。
