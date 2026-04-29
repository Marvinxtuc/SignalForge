# SignalForge Round 1 Staging Report

## 任务判断

结论：Round 1 staging 验证 PASS。

依据：本地 Docker Compose staging runtime 已由 QA 报告验证通过；same-origin `/api/*`、API pytest、Web production build、no-secrets、frontend MVP validation 均通过。

## 当前目标

- 确认 Round 1 candidate 在 staging-like Docker Compose 环境中可运行。
- 确认浏览器访问模型为 Web 同源 `/api/*`。
- 确认平台筛选、健康检查、项目列表、平台设置接口满足 demo 验证要求。

## 已确认事实

- `docker compose -f infra/docker-compose.yml build`：PASS。
- `docker compose -f infra/docker-compose.yml up -d`：PASS。
- `docker compose -f infra/docker-compose.yml run --rm api pytest`：PASS，`123 passed in 2.76s`。
- `docker compose -f infra/docker-compose.yml run --rm web npm run build`：PASS。
- `curl -i http://localhost:3000/api/health`：PASS，HTTP 200。
- `curl -i 'http://localhost:3000/api/projects?page_size=1'`：PASS，HTTP 200。
- `curl -i http://localhost:3000/api/settings/platforms`：PASS，HTTP 200。
- `python3 scripts/validate_no_secrets.py`：PASS。
- `python3 scripts/validate_frontend_mvp.py --require-http`：PASS。
- Running web container bundle 未发现 `http://localhost:8000`。
- 真实 external smoke 已通过临时 Cloudflare tunnel：`https://subdivision-observer-females-karma.trycloudflare.com/...&sf_token=<redacted>`。

## 风险点

- 本地 staging-like 环境不等价于正式生产环境。
- Docker Compose buildx warning 不阻断验证，但属于环境提示。
- Stale local `.next` cache artifact 不属于 running web container bundle，QA 已判定非 Go 风险。

## 推荐方案

Round 1 staging 可接受，进入 external demo smoke 与 Go/No-Go 决策。

## 改动边界

- 本报告仅汇总 staging 验证结果。
- 未修改应用代码。
- 未执行 git 暂存、提交、重置或回滚。

## 执行命令

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
docker compose -f infra/docker-compose.yml ps
```

## 验证结果

PASS。

## 残留问题

- 无 staging Go-blocking 残留问题。

## 回滚方式

- 停止 staging runtime：

```bash
docker compose -f infra/docker-compose.yml down
```

- 如需回滚本报告，恢复或删除 `staging_report.md`。
