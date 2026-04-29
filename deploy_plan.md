# SignalForge Round 1 Deploy Plan

## 任务判断

结论：Round 1 可按外部 demo 上线验证流程部署。部署范围限定为 Web 外部访问修复、同源 API proxy、平台筛选升级、Runtime 环境变量与 CORS 配置，不包含正式生产发布。

## 当前目标

- 使用 Docker Compose 启动 `api`、`web`、`postgres`、`redis`。
- Web 通过服务端环境变量 `SERVER_API_BASE_URL=http://api:8000` 访问 API。
- 外部 tunnel 只暴露 Web，不暴露内部 API。
- 通过同源 `/api/*` 与 external smoke 完成上线验证。

## 已确认事实

- `architecture_plan.md` 指定架构为 Browser -> Next.js Route Handler runtime proxy -> FastAPI。
- `runtime_plan.md` 指定 Compose 内部 API 地址为 `http://api:8000`。
- `frontend_change_report.md` 记录已新增 same-origin Next route handler proxy。
- `qa_test_report.md` 记录 Docker build、服务启动、API tests、Web build、本地 same-origin API smoke 均通过。
- `external_smoke_report.md` 记录用户批准的临时 Cloudflare tunnel smoke PASS。
- `security_review.md` 确认 `sf_token` query 被脱敏并不会转发到 FastAPI。

## 推荐方案

1. 以当前工作树作为 Round 1 demo candidate。
2. 使用 Docker Compose 构建并启动本地 runtime。
3. 仅将 Web 服务 `localhost:3000` 暴露给外部 tunnel。
4. 使用 `scripts/validate_external_smoke.py` 验证外部页面与 same-origin API。
5. 验证通过后记录 staging、production demo 验证报告和 Go/No-Go 结论。

## 改动边界

允许范围：

- 发布管理文档。
- Docker Compose runtime 配置验证。
- 外部 demo smoke 验证。

禁止范围：

- 不执行 `git add`、`git commit`、`git reset`、`git revert`。
- 不删除文件。
- 不覆盖配置。
- 不做批量重构。
- 不修改数据库 schema 或 migration。
- 不调用真实 Reddit、Product Hunt、X、Discord 或其他外部平台 API。
- 不写入完整 `sf_token`，只记录 `sf_token=<redacted>`。

## 实施步骤

1. 构建镜像：

```bash
docker compose -f infra/docker-compose.yml build
```

2. 启动服务：

```bash
docker compose -f infra/docker-compose.yml up -d
```

3. 检查服务状态：

```bash
docker compose -f infra/docker-compose.yml ps
```

4. 验证本地 same-origin API：

```bash
curl -i http://localhost:3000/api/health
curl -i 'http://localhost:3000/api/projects?page_size=1'
curl -i http://localhost:3000/api/settings/platforms
```

5. 验证测试与构建：

```bash
docker compose -f infra/docker-compose.yml run --rm api pytest
docker compose -f infra/docker-compose.yml run --rm web npm run build
python3 scripts/validate_no_secrets.py
python3 scripts/validate_frontend_mvp.py --require-http
```

6. 启动外部 tunnel 指向 Web `localhost:3000`。

7. 执行 external smoke：

```bash
python3 scripts/validate_external_smoke.py --url 'https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>' --check-api
```

## 验证标准

- Compose services running。
- `/api/health` HTTP 200。
- `/api/projects?page_size=1` HTTP 200。
- `/api/settings/platforms` HTTP 200。
- API pytest PASS。
- Web production build PASS。
- no-secrets PASS。
- frontend MVP validation PASS。
- external smoke PASS。
- 报告中不得出现完整 `sf_token`。
- 临时 tunnel 验证完成后应停止。

## 风险点

- 外部 tunnel 稳定性不属于应用本身能力，可能受网络或 tunnel 服务影响。
- `sf_token` 仅适用于临时 demo 访问控制。
- 本轮不是正式生产部署，不覆盖长期鉴权、正式域名、TLS 证书、监控告警、备份恢复与容量验证。

## 回滚方式

- 停止 demo runtime：

```bash
docker compose -f infra/docker-compose.yml down
```

- 关闭外部 tunnel。
- 如需代码层回滚，按各 subagent 报告中的文件清单恢复对应变更。
