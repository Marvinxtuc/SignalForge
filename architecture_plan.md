# SignalForge Round 1 Architecture Gate

## 任务判断

结论：**Architecture Gate: PASS**。

当前仓库源码与 Docker 结构已经满足 Round 1 架构门禁：浏览器侧默认并在 Docker 场景下走同源 `/api/*`；Next Route Handler 负责 runtime proxy；Web 容器使用 `SERVER_API_BASE_URL=http://api:8000` 指向 Docker 内部 FastAPI；`/api/health` 映射 FastAPI `/health`；外部 tunnel 只需要暴露 Web 同源入口。

## 当前目标

锁定并复核以下 6 个门禁项：

| 门禁项 | 判定 | 关键依据 |
| --- | --- | --- |
| Next route handler proxy | PASS | `apps/web/app/api/[...path]/route.ts` 存在，导出 `GET/POST/PUT/PATCH/DELETE/OPTIONS/HEAD`，统一调用 `proxyBackendRequest`。 |
| `SERVER_API_BASE_URL=http://api:8000` | PASS | `infra/docker-compose.yml` 的 `web.environment.SERVER_API_BASE_URL` 已设置为 `http://api:8000`；`apps/web/lib/constants.ts` 默认服务端 base 也是 `http://api:8000`。 |
| 浏览器不请求 `localhost:8000` | PASS | Web 源码默认浏览器 base 为 `/api`；业务源码中直接 `fetch` 只集中在 `apps/web/lib/api.ts` 和 proxy route；Docker 不设置 `NEXT_PUBLIC_API_BASE_URL`。 |
| `/api/health` 映射 FastAPI `/health` | PASS | `apps/web/lib/api.ts` 将 `/health` 转为 `/api/health`；proxy route 将 `path === "health"` 转发为 `/health`；FastAPI 定义 `GET /health`。 |
| Docker standalone runtime env 生效 | PASS | `apps/web/next.config.mjs` 使用 `output: "standalone"`；`apps/web/Dockerfile` 运行 `node server.js`；route handler 在 Node runtime 读取 `process.env.SERVER_API_BASE_URL`。 |
| 外部 tunnel 走同源 `/api` | PASS | 浏览器默认 `PUBLIC_API_BASE_URL="/api"`；外部 smoke 脚本验证路径为 `/api/health`、`/api/projects`、`/api/settings/platforms`。 |

## 已确认事实

- `apps/web/app/api/[...path]/route.ts` 是 Next App Router catch-all Route Handler，声明 `runtime = "nodejs"` 与 `dynamic = "force-dynamic"`。
- 该 Route Handler 使用 `SERVER_API_BASE_URL` 构造上游 URL，并把非 health 的 `/api/*` 保持转发到 FastAPI `/api/*`。
- 该 Route Handler 在 query 转发时剥离 `sf_token`，并阻断 `authorization`、`cookie`、`sf-token`、`sf_token`、`x-sf-token` 等请求头。
- `apps/web/lib/api.ts` 拒绝调用方传入绝对 URL，浏览器侧默认把 `/health` 转为 `/api/health`，把其他后端路径转为同源 `/api/*`。
- `apps/web/lib/constants.ts` 中 `DEFAULT_PUBLIC_API_BASE_URL="/api"`，`DEFAULT_SERVER_API_BASE_URL="http://api:8000"`。
- `infra/docker-compose.yml` 的 Web 服务只设置 `SERVER_API_BASE_URL`，未设置 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`。
- `apps/web/next.config.mjs` 已启用 standalone 输出。
- `apps/web/Dockerfile` 使用 `.next/standalone` 并以 `node server.js` 启动。
- `apps/api/app/main.py` 定义 FastAPI `GET /health`。
- 本地同源请求 `GET http://localhost:3000/api/health` 返回 FastAPI health JSON。

## 风险点

- `NEXT_PUBLIC_API_BASE_URL` 仍作为可选覆盖存在。当前 Docker 未设置该变量，生产外部 host 对 localhost public base 有防护；但发布/隧道环境必须继续保持不设置该变量，或只设置为同源相对路径。
- 当前工作区存在 `.next` 旧构建残留，其中可检索到历史 `localhost:8000` 字符串。该目录是生成物，不作为本轮源码架构判定依据；进入正式 runtime 验证前必须重新构建 standalone 镜像或清理旧构建。
- 本轮未执行 Docker 镜像重建和容器内 runtime env 变更测试；Docker standalone runtime env 的 PASS 基于源码、Dockerfile 与 compose 结构判断。
- `README.md`、runbook 与脚本中保留本地开发直连 `localhost:8000` 的说明或默认值；这些不是浏览器业务请求路径，但后续文档审计可单独收敛。

## 推荐方案

保持当前架构，不进入额外重构：

1. 浏览器业务请求统一使用同源 `/api/*`。
2. Next Route Handler 作为浏览器 API 入口，转发到 Docker 内部 FastAPI。
3. Docker Web 运行时通过 `SERVER_API_BASE_URL=http://api:8000` 指向 `api` 服务。
4. 外部 tunnel 只暴露 Web 服务，不要求暴露 FastAPI 8000。
5. 正式 runtime 验证前重新构建 Web standalone，避免使用旧 `.next` 产物。

## 改动边界

本轮 Architecture Agent 只产出文档：

- 修改：`architecture_plan.md`
- 未修改：Next 源码、FastAPI 源码、Docker 配置、测试脚本、环境变量文件
- 未生成：`blocking_issue.md`，因为 Architecture Gate 判定为 PASS

## 实施步骤

已执行：

1. 读取仓库文件清单与 git 状态，确认存在他人/既有改动，不回滚、不覆盖代码。
2. 读取 Next route handler、API client、constants、Next config、Web Dockerfile、Docker compose、FastAPI main/config。
3. 搜索 `localhost:8000`、`SERVER_API_BASE_URL`、`NEXT_PUBLIC_API_BASE_URL`、`/api/health`、`/health` 相关引用。
4. 运行现有前端静态验收脚本。
5. 通过本地同源 URL 验证 `/api/health` 和 `/api/projects` 可经 Web 入口返回后端响应。
6. 更新根目录 `architecture_plan.md`，给出明确 PASS/FAIL 门禁结论。

## 验证标准

当前门禁通过标准如下：

- `apps/web/app/api/[...path]/route.ts` 存在并实现 runtime proxy。
- `infra/docker-compose.yml` 中 `web.environment.SERVER_API_BASE_URL=http://api:8000`。
- Web Docker 配置不把 `NEXT_PUBLIC_API_BASE_URL` 设置为 `http://localhost:8000`。
- 浏览器默认 API base 为同源 `/api`。
- `api.health()` 对应浏览器路径 `/api/health`。
- Route Handler 将 `/api/health` 上游映射为 FastAPI `/health`。
- Next 使用 standalone 构建输出并以 Node server runtime 启动。
- 外部 smoke 路径为同源 `/api/*`。

## 关键依据

- `apps/web/app/api/[...path]/route.ts:1` 引入 `SERVER_API_BASE_URL`。
- `apps/web/app/api/[...path]/route.ts:3` 声明 `dynamic = "force-dynamic"`。
- `apps/web/app/api/[...path]/route.ts:4` 声明 `runtime = "nodejs"`。
- `apps/web/app/api/[...path]/route.ts:57` 统一代理入口 `proxyBackendRequest`。
- `apps/web/app/api/[...path]/route.ts:98` 将 health 特例映射为 `/health`，其他路径映射为 `/api/${path}`。
- `apps/web/app/api/[...path]/route.ts:99` 使用 `SERVER_API_BASE_URL` 构造上游地址。
- `apps/web/lib/constants.ts:1` 默认 `DEFAULT_SERVER_API_BASE_URL = "http://api:8000"`。
- `apps/web/lib/constants.ts:5` 默认 `DEFAULT_PUBLIC_API_BASE_URL = "/api"`。
- `apps/web/lib/api.ts:103` 拒绝绝对后端 path。
- `apps/web/lib/api.ts:127` 按 server/browser 环境解析 API URL。
- `apps/web/lib/api.ts:145` 浏览器 health 映射 `/api/health`。
- `infra/docker-compose.yml:22` Web 服务环境变量段。
- `infra/docker-compose.yml:23` `SERVER_API_BASE_URL: http://api:8000`。
- `apps/web/next.config.mjs:3` `output: "standalone"`。
- `apps/web/Dockerfile:19` 复制 `.next/standalone`。
- `apps/web/Dockerfile:32` 使用 `node server.js` 启动。
- `apps/api/app/main.py:44` FastAPI `GET /health`。
- `scripts/validate_external_smoke.py:15` 外部 smoke 使用同源 `/api/*` 路径。

## 执行命令

```bash
pwd && rg --files -g '!*node_modules*' -g '!*.next*' -g '!__pycache__*'
find . -maxdepth 3 -name 'package.json' -o -name 'next.config.*' -o -name 'Dockerfile*' -o -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'main.py' -o -name 'app.py' -o -name 'requirements*.txt' -o -name 'pyproject.toml'
git status --short
sed -n '1,260p' 'apps/web/app/api/[...path]/route.ts'
sed -n '1,260p' infra/docker-compose.yml
sed -n '1,240p' apps/web/Dockerfile
sed -n '1,260p' apps/web/lib/api.ts
sed -n '1,220p' apps/web/lib/constants.ts
sed -n '1,180p' apps/web/next.config.mjs
sed -n '1,260p' apps/api/app/main.py
sed -n '1,160p' apps/api/app/config.py
rg -n "localhost:8000|127\\.0\\.0\\.1:8000|api:8000|NEXT_PUBLIC_API_BASE_URL|SERVER_API_BASE_URL|/api/health|/health" apps/web apps/api infra .env.example README.md docs scripts -g '!*node_modules*'
rg -n "fetch\\(|axios|XMLHttpRequest|localhost:8000|127\\.0\\.0\\.1:8000" apps/web/app apps/web/components apps/web/lib -g '!*.d.ts'
python3 scripts/validate_frontend_mvp.py
curl -sS -i --max-time 5 http://localhost:3000/api/health
curl -sS -i --max-time 5 'http://localhost:3000/api/projects?page_size=1'
```

## 验证结果

- `python3 scripts/validate_frontend_mvp.py`：PASS，包含 “API client is limited to the SignalForge backend boundary” 与 “frontend MVP validation succeeded”。
- `GET http://localhost:3000/api/health`：HTTP 200，返回 `{"status":"ok","service":"signalforge-api","phase":"phase-2-backend-api"}`。
- `GET http://localhost:3000/api/projects?page_size=1`：HTTP 200，返回 FastAPI 项目列表 JSON。
- 源码搜索确认：`apps/web/app`、`apps/web/components`、`apps/web/lib` 中直接 `fetch` 仅出现在 `apps/web/lib/api.ts` 和 `apps/web/app/api/[...path]/route.ts`。
- Docker compose 确认：Web 服务使用 `SERVER_API_BASE_URL=http://api:8000`，未设置 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`。

## 残留问题

- 未执行 Docker 镜像 rebuild 与容器内 runtime env smoke；建议由 Runtime/QA Agent 在编码后或 release 前执行。
- `.next` 旧生成物存在历史 `localhost:8000` 字符串；正式验证必须以重新构建产物为准。
- 文档与本地脚本中仍有开发直连 `localhost:8000` 示例；不阻塞本轮架构门禁。

## 回滚方式

本轮只修改 `architecture_plan.md`：

```bash
git checkout -- architecture_plan.md
```

如需保留当前报告但撤销本轮内容，可从版本控制恢复该文件到修改前状态。由于未改代码、配置或数据，不涉及服务回滚、迁移回滚或密钥轮换。
