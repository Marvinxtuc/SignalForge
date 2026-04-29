# SignalForge Round 1 Architecture Plan

## 任务判断

结论：Round 1 架构锁定为 **Browser -> Next.js Route Handler runtime proxy -> FastAPI**。浏览器只访问 Web 同源 `/api/*`，不得直接请求 `localhost:8000` 或任何 FastAPI 绝对地址；Next.js 服务端使用 `SERVER_API_BASE_URL=http://api:8000` 转发到 Docker 内部 API 服务。

依据：
- `apps/web/next.config.mjs` 当前启用 `output: "standalone"`，适合 Docker standalone runtime。
- `apps/web/lib/api.ts` 当前业务调用路径已使用 `/api/*`，但 URL base 依赖公开变量。
- `infra/docker-compose.yml` 当前 Web 容器配置 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`，会让外部浏览器暴露并请求不可达后端地址。
- `apps/api/app/main.py` 已有 FastAPI `/health`，但未提供 `/api/health`。
- `apps/api/app/main.py` 当前 CORS 来源硬编码为本地开发地址。

## 当前目标

1. 浏览器所有业务 API 请求固定走同源 `/api/*`。
2. Next Route Handler 在运行时将 `/api/*` 转发到 FastAPI。
3. Docker standalone 运行时通过 `SERVER_API_BASE_URL=http://api:8000` 生效。
4. 外部 tunnel 只暴露 Web，同源 `/api` 由 Next 代理，不要求浏览器访问 FastAPI。
5. `/api/health` 在 Next 层映射到 FastAPI `/health`。
6. CORS 改为环境变量驱动，保留本地默认值。
7. `sf_token` 仅作为 demo query/cookie 访问控制使用，不转发到 FastAPI。

## 已确认事实

- `implementation_plan.md` 已限定 Round 1 不新增后端业务 API、不新增 migration、不调用真实外部平台 API、不写 token。
- `apps/web/lib/api.ts` 的业务 API path 形态为 `/api/projects`、`/api/signals/...` 等相对路径。
- `apps/web/next.config.mjs` 当前只有 `output: "standalone"`。
- `apps/api/app/main.py` 已注册业务 router，并定义 `GET /health`。
- `apps/api/app/main.py` 当前 CORS `allow_origins` 为 `http://localhost:3000` 和 `http://127.0.0.1:3000`。
- `apps/api/app/config.py` 当前只读取 `DATABASE_URL`、`REDIS_URL`。
- `infra/docker-compose.yml` 当前 `api` 服务名为 `api`，容器内 FastAPI 地址可采用 `http://api:8000`。
- `infra/docker-compose.yml` 当前 Web 服务仍使用公开环境变量 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`。

## 架构决策

### ADR-R1-001：Next Route Handler Runtime Proxy

Round 1 采用 Next.js Route Handler 作为 runtime proxy，而不是浏览器直连 FastAPI，也不是仅依赖 `next.config.mjs` rewrites。

判断：
- Route Handler 可在 standalone 容器运行时读取 `SERVER_API_BASE_URL`，避免 build-time 固化。
- Route Handler 可集中处理 `sf_token`、header 白名单、health 特例映射和错误响应。
- 浏览器请求始终保持同源，适配外部 tunnel、局域网访问和反向代理部署。

### ADR-R1-002：服务端后端地址

固定服务端环境变量：

```text
SERVER_API_BASE_URL=http://api:8000
```

约束：
- 该变量只在 Next 服务端读取。
- 不使用 `NEXT_PUBLIC_*` 暴露 FastAPI 地址。
- 浏览器 Network 中不得出现 `localhost:8000`、`127.0.0.1:8000`、`api:8000`。

### ADR-R1-003：Health 映射

同源接口：

```text
GET /api/health
```

Next 转发目标：

```text
GET {SERVER_API_BASE_URL}/health
```

说明：
- `/api/health` 是 Web 同源健康检查入口。
- FastAPI 保持现有 `/health`。
- 不要求 FastAPI 新增 `/api/health`。

### ADR-R1-004：sf_token 边界

`sf_token` 仅作为 demo 访问控制使用：
- 可从 query 或 cookie 读取。
- 只在 Next proxy 层校验。
- 不写入仓库。
- 不记录到日志。
- 不转发到 FastAPI。
- 不作为 FastAPI 鉴权方案。

## Browser -> Next -> FastAPI 数据流

```text
Browser
  |
  | same-origin fetch: /api/projects, /api/projects/:id/signals, /api/health
  | optional demo access token: sf_token in query or cookie
  v
Next.js Route Handler runtime proxy
  |
  | validates demo access when enabled
  | strips sf_token from query and headers
  | maps /api/health -> /health
  | maps /api/* business path -> /api/*
  | forwards allowed method/body/query to SERVER_API_BASE_URL
  v
FastAPI
  |
  | existing routers and /health
  v
JSON response returned through Next to Browser
```

## 接口契约

### 浏览器到 Next

基础规则：
- 请求 origin：Web 同源。
- 请求 path：仅 `/api/*`。
- 禁止浏览器请求 `http://localhost:8000/*`。
- 禁止浏览器读取或依赖 `SERVER_API_BASE_URL`。

支持方法：
- `GET`
- `POST`
- `PUT`
- `DELETE`
- `OPTIONS` 如运行时需要预检兼容

请求体：
- JSON body 原样转发。
- 空 body 保持为空。

Query：
- 普通业务 query 原样转发。
- `sf_token` 在 Next 层消费后必须剥离，不转发。

Header：
- 允许转发业务必要 header，例如 `Accept`、`Content-Type`。
- 不转发 demo token。
- 不新增平台 API token。

### Next 到 FastAPI

目标 base：

```text
SERVER_API_BASE_URL=http://api:8000
```

路径映射：

| Browser path | FastAPI path | 说明 |
| --- | --- | --- |
| `/api/health` | `/health` | 健康检查特例 |
| `/api/projects` | `/api/projects` | 保持业务 API 路径 |
| `/api/projects/{project_id}/signals` | `/api/projects/{project_id}/signals` | 保持现有筛选契约 |
| `/api/signals/{signal_id}` | `/api/signals/{signal_id}` | 保持现有业务契约 |

响应：
- FastAPI JSON 响应由 Next 原样返回。
- FastAPI status code 由 Next 保持。
- FastAPI error envelope 不改变。

### CORS 契约

目标：
- 浏览器正常场景只访问 Next 同源，因此业务路径不依赖浏览器跨域访问 FastAPI。
- FastAPI CORS 仍需环境变量化，服务本地开发、调试或受控部署。

建议环境变量：

```text
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

约束：
- 默认值仅覆盖本地开发。
- 外部 tunnel 域名如需直连 FastAPI 调试，必须显式配置。
- Round 1 正式访问路径仍为同源 `/api`，不是浏览器跨域直连 FastAPI。

## 环境变量

### Web / Next

| 变量 | 示例值 | 可见性 | 用途 |
| --- | --- | --- | --- |
| `SERVER_API_BASE_URL` | `http://api:8000` | 服务端 | Next runtime proxy 转发目标 |
| `SF_DEMO_ACCESS_TOKEN` | 不写入仓库 | 服务端 | 可选 demo 访问控制校验值 |
| `NEXT_PUBLIC_API_BASE_URL` | 不再需要 | 浏览器公开 | Round 1 不应继续用于后端绝对地址 |

Docker 要求：
- `web.environment.SERVER_API_BASE_URL=http://api:8000`。
- 不再通过 `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` 指导浏览器访问后端。
- standalone 容器启动时读取 runtime env，不能依赖构建期固化。

### API / FastAPI

| 变量 | 示例值 | 用途 |
| --- | --- | --- |
| `DATABASE_URL` | 现有值 | 数据库连接 |
| `REDIS_URL` | 现有值 | Redis 连接 |
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | CORS 来源列表 |

## No-Go 条件

以下任一情况出现即视为 Round 1 架构不通过：

1. 浏览器 Network 出现对 `localhost:8000`、`127.0.0.1:8000` 或 `api:8000` 的请求。
2. `SERVER_API_BASE_URL` 被写入 `NEXT_PUBLIC_*` 或前端 bundle。
3. `/api/health` 未能映射到 FastAPI `/health`。
4. Docker standalone Web 容器只能在 build-time 固化后端地址，runtime 修改环境变量不生效。
5. 外部 tunnel 访问时业务 API 仍依赖跨域请求 FastAPI。
6. `sf_token` 被转发到 FastAPI query、header 或 body。
7. 为 Round 1 新增数据库 migration。
8. 为 Round 1 新增或修改真实外部平台 token。
9. 为 Round 1 调用 Reddit、Product Hunt、X、Discord 或其他外部平台 API。
10. 修改后端业务数据模型、生产采集逻辑、评分逻辑或机会生成逻辑。

## 改动边界

允许后续实现修改：
- Next Route Handler proxy 文件。
- Web API client base 策略。
- Docker compose Web 环境变量。
- FastAPI CORS 配置读取环境变量。
- 前端平台筛选 UI。

不允许后续实现修改：
- 数据库 schema。
- migration。
- 后端业务 router 契约。
- 外部平台集成 token。
- 真实外部平台调用逻辑。
- 与 Round 1 无关的批量重构。

## 实施步骤

1. 新增 Next Route Handler 捕获 `/api/*`。
2. 在 Route Handler 中读取 `SERVER_API_BASE_URL`，默认开发值可为 `http://localhost:8000`，Docker 值必须为 `http://api:8000`。
3. 实现 `/api/health` 到 `/health` 的路径特例。
4. 对业务 `/api/*` 保持路径转发。
5. 在 Next 层消费并剥离 `sf_token`。
6. 调整 Web API client，默认使用同源 `/api/*`，不再要求公开后端 base URL。
7. 调整 Docker Web 环境变量为 `SERVER_API_BASE_URL=http://api:8000`。
8. 将 FastAPI CORS origins 改为环境变量读取。
9. 执行类型检查、构建和 Docker runtime 验证。

## 验证标准

- 浏览器请求业务接口时 Network URL 为同源 `/api/*`。
- 浏览器不请求 `localhost:8000`。
- `GET /api/health` 返回 FastAPI `/health` 的 JSON。
- Docker Web standalone 容器启动后读取 `SERVER_API_BASE_URL=http://api:8000`。
- 外部 tunnel 访问 Web 时，业务 API 仍走同源 `/api`。
- FastAPI CORS origins 可通过 `BACKEND_CORS_ORIGINS` 配置。
- 带 `sf_token` 的 demo 访问可在 Next 层通过，但 FastAPI 收不到 `sf_token`。
- 未新增 migration。
- 未写入 token。
- 未调用外部平台 API。

## 回滚方式

架构文档回滚：
- 删除 `architecture_plan.md`。

后续实现回滚建议：
- 删除 Next Route Handler proxy。
- 恢复 Web API client 到实现前 base URL 策略。
- 恢复 Docker Web 环境变量。
- 恢复 FastAPI CORS 硬编码配置。
- 移除 demo `sf_token` proxy 校验逻辑。

## Subagent Report: Architecture Agent

### 检查文件

- `implementation_plan.md`
- `apps/web/lib/api.ts`
- `apps/web/next.config.mjs`
- `apps/api/app/main.py`
- `apps/api/app/config.py`
- `infra/docker-compose.yml`

### 修改文件

- `architecture_plan.md`

### 是否通过

通过。

说明：
- Round 1 架构已锁定为 Next Route Handler runtime proxy。
- 已明确 `SERVER_API_BASE_URL=http://api:8000`。
- 已明确浏览器不得请求 `localhost:8000`。
- 已明确 `/api/health` 映射 FastAPI `/health`。
- 已明确 Docker standalone runtime env 必须生效。
- 已明确外部 tunnel 走同源 `/api`。
- 已明确 CORS 环境变量方案。
- 已明确 `sf_token` 只作为 demo query/cookie 访问控制，不转发到 FastAPI。
