# SignalForge Round 1 QA Test Report

## PASS/FAIL

PASS

结论：本轮指定功能与构建验证通过。未发现需要写入 `blocking_issue.md` 的阻塞问题。

## 任务判断

- 角色：SignalForge Round 1 QA Agent。
- 工作目录：`/Users/marvin.x/Desktop/SignalForge`。
- 写入边界：仅更新 `qa_test_report.md`；未修改业务源码、配置、迁移或测试代码。
- 验证重点：`docker compose build/up`、API pytest、Web build、no-secrets、Frontend MVP `--require-http`、同源 API、平台选择、query 保留、浏览器/源码不请求 `localhost:8000`。

## 已确认事实

- `docker compose -f infra/docker-compose.yml ps` 执行前已有 `api`、`web`、`postgres`、`redis` 容器运行。
- `docker compose build` 成功构建 `infra-api:latest` 与 `infra-web:latest`。
- `docker compose up -d` 成功启动服务，并重建了 `api`、`web` 容器。
- API 容器内 pytest 全部通过：`123 passed in 1.07s`。
- Web 本地 `npm run build` 成功，Next.js 生成 9 个 app routes。
- `no-secrets` 验证通过。
- `frontend MVP --require-http` 验证通过。
- 同源 `http://localhost:3000/api/health`、`/api/projects?page_size=1`、`/api/settings/platforms` 均返回 `HTTP 200`。
- `SignalFilters` 渲染/源码包含 `<option value="product_hunt">Product Hunt</option>`。
- 导航链接保留 `projectId=qa-project` 与 `sf_token=qa-token`。
- `apps/web` 源码、`.next` 构建产物与 HTTP 渲染页面未发现 `localhost:8000` 或 `127.0.0.1:8000`。

## 执行命令

1. `pwd && rg --files -g '!*node_modules*' -g '!*.png' -g '!*.jpg' -g '!*.jpeg' -g '!*.gif' | head -200`
   - 结果：PASS
   - 目的：确认工作目录和项目结构。

2. `ls -la`
   - 结果：PASS
   - 目的：确认根目录文件状态。

3. `git status --short`
   - 结果：PASS
   - 目的：确认已有改动，避免回滚或覆盖其他 agent 改动。
   - 备注：工作区已有多处未提交改动，未回滚。

4. `docker compose -f infra/docker-compose.yml ps`
   - 结果：PASS
   - 验证结果：执行前已有 `api`、`web`、`postgres`、`redis` 运行。

5. `docker compose -f infra/docker-compose.yml build`
   - 结果：PASS
   - 验证结果：API 与 Web 镜像均成功构建。
   - 备注：Docker Compose 提示未安装 buildx plugin；不影响本次 classic builder 构建成功。

6. `docker compose -f infra/docker-compose.yml up -d`
   - 结果：PASS
   - 验证结果：`postgres`、`redis` healthy；`api`、`web` started。

7. `docker compose -f infra/docker-compose.yml ps`
   - 结果：PASS
   - 验证结果：`api`、`web`、`postgres`、`redis` 均 Up；`web` 映射 `3000:3000`，`api` 映射 `8000:8000`。

8. `python3 -m pytest apps/api/tests`
   - 结果：FAIL（环境入口失败）
   - 验证结果：本机 `/opt/homebrew/opt/python@3.14/bin/python3.14` 未安装 pytest：`No module named pytest`。
   - 判断：非应用测试失败；为避免安装依赖或越界写入，改用已构建 API 容器执行 pytest。

9. `docker compose -f infra/docker-compose.yml exec -T api pytest tests`
   - 结果：PASS
   - 验证结果：`123 passed in 1.07s`。

10. `npm run build`
    - 工作目录：`/Users/marvin.x/Desktop/SignalForge/apps/web`
    - 结果：PASS
    - 验证结果：Next.js production build 成功；路由包含 `/`、`/api/[...path]`、`/dashboard`、`/logs`、`/opportunities`、`/opportunities/[id]`、`/reports`、`/settings`、`/signals`。

11. `python3 scripts/validate_no_secrets.py`
    - 结果：PASS
    - 验证结果：`PASS: no secrets validation`。

12. `python3 scripts/validate_frontend_mvp.py --require-http --base-url http://localhost:3000`
    - 结果：PASS
    - 验证结果：Required pages、UI markers、API client boundary、query helper、platform select、forbidden token/real execution options、HTTP smoke 全部通过。

13. `curl -sS -i http://localhost:3000/api/health`
    - 结果：PASS
    - 验证结果：`HTTP/1.1 200 OK`；body 为 `{"status":"ok","service":"signalforge-api","phase":"phase-2-backend-api"}`。

14. `curl -sS -i 'http://localhost:3000/api/projects?page_size=1'`
    - 结果：PASS
    - 验证结果：`HTTP/1.1 200 OK`；返回 `items` 1 条、`page_size: 1`、`total: 35`。

15. `curl -sS -i http://localhost:3000/api/settings/platforms`
    - 结果：PASS
    - 验证结果：`HTTP/1.1 200 OK`；返回 `reddit`、`product_hunt`、`x`、`discord`，其中 `reddit` 与 `product_hunt` 为 MVP enabled。

16. `rg -n "localhost:8000|127\\.0\\.0\\.1:8000|http://localhost:8000|http://127\\.0\\.0\\.1:8000" apps/web --glob '!node_modules/**' --glob '!.next/**'`
    - 结果：PASS
    - 验证结果：无匹配。

17. `rg -n "product_hunt|Product Hunt|<select|buildAllowedQueryHref|sf_token|projectId" apps/web/components apps/web/lib apps/web/app --glob '!node_modules/**' --glob '!.next/**'`
    - 结果：PASS
    - 验证结果：确认 `product_hunt`、`Product Hunt`、`buildAllowedQueryHref`、`projectId`、`sf_token` 在预期组件/工具中存在。

18. `curl -sS 'http://localhost:3000/signals?projectId=qa-project&sf_token=qa-token' | rg -n "localhost:8000|127\\.0\\.0\\.1:8000|product_hunt|Product Hunt|qa-project|qa-token"`
    - 结果：PASS
    - 验证结果：渲染 HTML 包含 `value="product_hunt"`、`Product Hunt`，导航 href 保留 `projectId=qa-project` 与 `sf_token=qa-token`；未出现 `localhost:8000` 或 `127.0.0.1:8000`。

19. `rg -n "localhost:8000|127\\.0\\.0\\.1:8000|http://localhost:8000|http://127\\.0\\.0\\.1:8000" apps/web/.next apps/web --glob '!node_modules/**'`
    - 结果：PASS
    - 验证结果：无匹配。

20. `for route in '/' '/signals?projectId=qa-project&sf_token=qa-token' '/dashboard?projectId=qa-project&sf_token=qa-token' '/opportunities?projectId=qa-project&sf_token=qa-token' '/logs?projectId=qa-project&sf_token=qa-token' '/settings?projectId=qa-project&sf_token=qa-token' '/reports?projectId=qa-project&sf_token=qa-token'; do if curl -sS "http://localhost:3000${route}" | rg -q 'localhost:8000|127\\.0\\.0\\.1:8000'; then echo "FAIL ${route}"; else echo "PASS ${route}"; fi; done`
    - 结果：PASS
    - 验证结果：所有 listed routes 均输出 PASS。

## 覆盖项结果

| 覆盖项 | 结果 | 依据 |
| --- | --- | --- |
| docker compose build | PASS | `infra-api:latest`、`infra-web:latest` 构建成功 |
| docker compose up | PASS | 四个服务均 Up，Postgres/Redis healthy |
| api pytest | PASS | 容器内 `pytest tests`：`123 passed in 1.07s` |
| web npm run build | PASS | Next.js production build 成功 |
| no-secrets | PASS | `PASS: no secrets validation` |
| frontend MVP --require-http | PASS | `PASS: frontend MVP validation succeeded` |
| 同源 `/api/health` | PASS | `HTTP 200`，返回 API health JSON |
| 同源 `/api/projects?page_size=1` | PASS | `HTTP 200`，返回 1 条 project |
| 同源 `/api/settings/platforms` | PASS | `HTTP 200`，返回四个平台 |
| platform select | PASS | signals 页面和源码包含 platform `<select>` |
| Product Hunt value `product_hunt` | PASS | 渲染 HTML 包含 `value="product_hunt">Product Hunt` |
| 导航保留 `projectId` 与 `sf_token` | PASS | signals/dashboard 渲染导航 href 均保留两个 query |
| 源码不请求 `localhost:8000` | PASS | `apps/web` 源码无匹配 |
| 构建产物/HTTP 渲染不请求 `localhost:8000` | PASS | `.next` 与主要路由渲染输出无匹配 |

## 风险点

- 本机 Python 3.14 环境未安装 pytest，直接 `python3 -m pytest apps/api/tests` 无法作为本地入口使用。
- Browser Use in-app backend 不可用：`Failed to connect to browser-use backend "iab". No Codex IAB backends were discovered.` 因此未能通过真实浏览器 DevTools 网络面板采集请求列表。
- `docker compose up -d` 按任务要求执行，重建了本地 `api` 与 `web` 容器；未停止或删除任何容器/卷。

## 残留问题

- 非阻断：本机 pytest 入口缺依赖。最小修复建议是在项目约定中明确使用容器 pytest，或由负责环境的 agent 创建本地虚拟环境并安装 `apps/api/requirements.txt`。
- 非阻断：Browser Use 后端不可用。最小修复建议是恢复 Codex in-app browser backend 后补跑真实浏览器网络检查；当前已用源码、构建产物与 HTTP 渲染输出补充验证。

## 修改文件清单

- `qa_test_report.md`

## 改动目的

- 记录 SignalForge Round 1 QA 的执行命令、验证结果、残留问题与回滚方式，供总控与审计系统复核。

## 回滚方式

- 本轮未修改源码、配置、迁移或数据文件。
- 若需回滚报告：从版本控制或上一份审计备份恢复 `qa_test_report.md`。
- 若需回滚本轮 compose 启动状态：可执行 `docker compose -f infra/docker-compose.yml down`。注意该命令会停止并移除本地 compose 容器，但不会删除命名卷；执行前应由总控确认是否影响其他 agent。
