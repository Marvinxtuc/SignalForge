# SignalForge Round 1 Implementation Plan

## 任务判断

结论：PASS。

Round 1 可以进入前端最小改动实施，无需数据结构调整、数据库迁移或后端业务 API 变更。当前未发现阻塞项，因此不生成 `blocking_issue.md`。

依据：
- Round 1 目标集中在外部访问可用性和信号收件箱筛选体验。
- 仓库现有后端已提供 `/health` 与 `/api/*` 业务接口，信号列表接口已有 `platform` 查询参数。
- 仓库现状已出现与 Round 1 相关的前端未提交改动痕迹，包括同源 proxy route、query helper、平台 select、backend status 展示；本计划仅定义实施与验收边界，不评价这些未提交改动是否已完成验收。

## 当前目标

1. 将浏览器侧后端访问改为前端同源 `/api/*` 路径，避免外部访问时暴露或依赖 `localhost:8000`。
2. 新增前端同源 proxy，由 Next.js 前端层转发到既有 FastAPI 后端。
3. 将信号收件箱 `platform` 筛选从自由文本升级为受控选项。
4. 增加或保留前端 query helper，保证跨页面导航只携带批准的查询参数。
5. 增加或保留前端 backend status 展示，便于用户识别后端连接状态。
6. 不新增后端业务 API，不改变数据结构，不调用真实外部平台。

## 已确认事实

- 当前工作目录为 `/Users/marvin.x/Desktop/SignalForge`。
- 仓库根目录已有 `implementation_plan.md`。
- `git status --short` 显示多处未提交改动，本计划只修改 `implementation_plan.md`。
- `apps/web/lib/constants.ts` 当前存在 `SERVER_API_BASE_URL`、`PUBLIC_API_BASE_URL` 和默认同源 `/api` 策略。
- `apps/web/app/api/[...path]/route.ts` 当前存在 Next.js route handler，用于将前端 `/api/*` 请求转发到后端。
- `apps/web/lib/api.ts` 当前集中构造后端请求 URL，并限制绝对外部 URL。
- `apps/web/lib/query.ts` 当前存在允许列表式 query helper。
- `apps/web/components/signals/SignalFilters.tsx` 当前平台筛选已呈现为 `<select>`，选项包含 `reddit`、`product_hunt`、`x`、`discord`。
- `apps/web/components/signals/SignalInbox.tsx` 当前会将非空 `filters.platform` 传入 `SignalListParams.platform`。
- `apps/web/components/layout/AppShell.tsx` 当前存在 backend status 状态与展示逻辑。
- 后端 `apps/api/app/main.py` 存在 `/health`。
- Round 1 未要求新增后端业务 API。

## 判断

- Round 1 的最小可行方案应限制在 `apps/web` 前端边界内。
- 现有后端 API 能支撑本轮需求；如发现前端请求失败，应优先排查 proxy、环境变量和路径映射，而不是新增后端接口。
- 当前仓库已有相关未提交改动，后续实施 agent 应先复核这些改动是否符合本计划，再决定是否补齐或修正。

## 待验证事项

- Docker Compose 与本地开发环境中 `SERVER_API_BASE_URL` 是否都能解析到后端服务。
- `/api/health` 是否正确映射到后端 `/health`。
- `/api/<path>` 是否正确映射到后端 `/api/<path>`，且 query 参数未丢失。
- 生产外部访问时浏览器 Network 是否只请求同源 `/api/*`。
- 平台筛选选择“全部平台”时是否不发送 `platform` 参数。

## 功能模块拆分

### 模块 1：前端同源 Proxy

目标：浏览器只访问 Web 同源 `/api/*`，由 Next.js 前端层代理到 FastAPI。

实施要点：
- 使用 Next.js route handler 或 rewrite 实现 `/api/*` 代理。
- `/api/health` 映射到后端 `/health`。
- 其他 `/api/<path>` 映射到后端 `/api/<path>`。
- 后端目标地址使用服务端环境变量，例如 `SERVER_API_BASE_URL`。
- proxy 不转发敏感请求头，例如 cookie、authorization、sf_token 等。

验收：
- 外部浏览器看不到后端内网地址或 `localhost:8000`。
- `/api/health` 和至少一个业务接口可通过同源路径访问。

### 模块 2：前端 API Base

目标：前端 API client 默认使用同源 `/api`，避免生产浏览器依赖公开后端绝对地址。

实施要点：
- 默认 public API base 为 `/api`。
- 服务端渲染或 route handler 使用 `SERVER_API_BASE_URL` 访问后端。
- 继续拒绝任意 `http://` 或 `https://` path 输入，保持 API client 边界。
- 保留超时、错误解析、JSON 解析等既有行为。

验收：
- `api.health()` 在浏览器侧请求 `/api/health`。
- `api.signals.list()` 等业务调用仍通过集中 API client 发出。

### 模块 3：Platform Select

目标：将平台筛选从自由文本改为受控选择，减少无效输入。

实施要点：
- `SignalFilters` 的平台控件使用 `<select>`。
- 选项值固定为：
  - 空值：全部平台
  - `reddit`
  - `product_hunt`
  - `x`
  - `discord`
- 展示文案可使用 `Reddit`、`Product Hunt`、`X`、`Discord`，但提交值必须保留后端枚举/存储值。
- `SignalInbox` 继续将空值映射为 `undefined`，非空值映射为 `platform` query。

验收：
- 选择每个平台时，请求 query 中的 `platform` 值准确。
- 选择全部平台时，请求不包含 `platform`。

### 模块 4：Query Helper

目标：集中管理前端页面间允许透传的 query 参数，避免无关参数扩散。

实施要点：
- 保留或新增 `apps/web/lib/query.ts`。
- 只允许明确批准的查询参数，例如 `projectId`、`sf_token`。
- 导航、项目选择器、机会详情返回路径统一使用 helper 构造 href。
- 不扩大 token 使用范围，不将 token 写入日志或存储。

验收：
- 页面切换时 `projectId` 可保留。
- 未列入允许列表的 query 参数不会被透传。

### 模块 5：Backend Status

目标：在前端 Shell 中展示后端连接状态，降低外部访问故障定位成本。

实施要点：
- 启动时并行请求 `api.health()` 和项目列表。
- 根据结果展示 `connected`、`partial`、`unavailable`。
- backend status 仅用于 UI 提示，不改变业务 API 语义。

验收：
- 后端可用时显示已连接。
- health 或项目列表部分失败时显示部分可用。
- 两者均失败时显示不可用，并保留错误提示。

## 数据结构变化

明确无。

不修改：
- 数据库表结构。
- Alembic migration。
- Pydantic schema 字段。
- 前后端业务实体结构。
- 既有 enum 的业务含义。

## API 变化

新增前端同源 proxy，不新增后端业务 API。

具体说明：
- 浏览器访问路径新增或统一为 Web 同源 `/api/*`。
- Next.js 前端层负责将 `/api/*` 转发到既有 FastAPI 后端。
- FastAPI 现有 endpoint、请求参数、响应结构不变。
- 不新增、删除、重命名后端业务 endpoint。
- 不改变 `/api/projects/{project_id}/signals` 的 `platform` 查询语义。

## 前端改动点

1. `apps/web/app/api/[...path]/route.ts`
   - 新增前端同源 proxy route。
   - 处理 `/api/health` 与业务 `/api/*` 映射。
   - 过滤敏感 headers 和不应透传的 query。

2. `apps/web/lib/constants.ts`
   - 新增或调整 `SERVER_API_BASE_URL`。
   - 默认 `PUBLIC_API_BASE_URL` 为 `/api`。
   - 避免生产浏览器默认指向 `localhost:8000`。

3. `apps/web/lib/api.ts`
   - API base 改为默认同源。
   - 保持 backend-relative path 限制。
   - 保持 query 参数构造、超时和错误处理。

4. `apps/web/lib/query.ts`
   - 新增或保留 query helper。
   - 仅允许批准参数跨页面透传。

5. `apps/web/components/signals/SignalFilters.tsx`
   - 平台筛选改为 select。
   - 选项值与后端平台值保持一致。

6. `apps/web/components/signals/SignalInbox.tsx`
   - 保持平台 query 构造逻辑。
   - 空值不发送 `platform`。

7. `apps/web/components/layout/AppShell.tsx`
   - 新增或保留 backend status 展示。
   - 使用 health 与项目列表结果判断连接状态。

8. 相关导航组件
   - `Navigation`、`ProjectSelector`、机会卡片/详情等如需保留 `projectId`，统一使用 query helper。

## 风险点

### P0

- Proxy 映射错误导致所有业务请求不可用。
- `SERVER_API_BASE_URL` 在部署环境不可解析，外部访问仍失败。
- `/api/health` 与 `/api/*` 路径映射不一致，导致状态显示与业务请求结果冲突。
- Proxy 错误透传敏感 header 或 token，造成凭据泄露风险。

### P1

- 平台 select 的 value 与后端实际 `platform` 值不一致，导致筛选结果为空。
- API base 兼容逻辑过宽，允许生产浏览器继续访问 `localhost` 或任意外部 API。
- Query helper 允许列表配置不当，导致 `projectId` 丢失或无关 query 扩散。
- Backend status 判断过于粗糙，把部分接口故障误判为整体可用。

### P2

- 平台展示文案与技术值差异可能造成用户理解成本。
- 历史数据如存在非标准平台值，本轮 select 不提供筛选入口。
- 通用后端错误文案无法直接定位是 proxy、后端还是网络问题。
- 同源 proxy 增加一次转发，可能带来轻微延迟。

## 不做事项

- 不做代码实施以外的批量重构。
- 本 PM/Requirement Agent 不修改业务代码。
- 不新增后端业务 API。
- 不修改生产业务逻辑。
- 不修改数据库结构。
- 不新增 migration。
- 不执行数据迁移。
- 不写入、读取或提交真实 token、密钥、凭据。
- 不调用 Reddit、Product Hunt、X、Discord 或其他真实外部平台 API。
- 不修改部署权限、云资源或生产配置。
- 不执行 `git add`、`git commit`、`git reset`、`git revert`。
- 不回滚或覆盖其他 agent 的未提交代码改动。

## 改动边界

允许后续实施 agent 修改：
- `apps/web/app/api/[...path]/route.ts`
- `apps/web/lib/constants.ts`
- `apps/web/lib/api.ts`
- `apps/web/lib/query.ts`
- `apps/web/components/signals/SignalFilters.tsx`
- `apps/web/components/signals/SignalInbox.tsx`
- `apps/web/components/layout/AppShell.tsx`
- 必要的前端导航 href 调用点
- 必要的前端验证脚本或测试

禁止后续实施 agent 修改，除非另行审批：
- `apps/api/app/api/routes/*`
- `apps/api/app/services/*`
- `apps/api/app/db/*`
- `apps/api/migrations/*`
- 生产部署配置、密钥、权限相关文件

## 实施步骤

1. 复核当前未提交改动，确认是否已有 Round 1 实现痕迹。
2. 补齐或修正前端同源 proxy。
3. 调整 API base 策略为浏览器默认同源 `/api`。
4. 接入或复核 query helper 的允许列表。
5. 将平台筛选固定为 select，并确认 query 构造。
6. 接入或复核 backend status 展示。
7. 执行前端静态检查、构建或项目既有验证脚本。
8. 输出实施报告，列出修改文件、执行命令、验证结果、残留风险和回滚方式。

## 验证标准

- `implementation_plan.md` 存在于仓库根目录。
- 未生成 `blocking_issue.md`。
- 浏览器业务请求使用同源 `/api/*`。
- `/api/health` 成功映射到后端 `/health`。
- `/api/projects/...` 等业务请求成功映射到后端 `/api/projects/...`。
- 信号平台筛选为 select。
- 平台 select 包含空值、`reddit`、`product_hunt`、`x`、`discord`。
- 选择全部平台时不发送 `platform` query。
- 选择具体平台时发送准确 `platform` query。
- 页面导航只透传允许的 query 参数。
- backend status 能区分 connected、partial、unavailable。
- 没有新增 migration。
- 没有新增后端业务 API。
- 没有写入 token、密钥或真实平台凭据。
- 没有调用真实外部平台 API。

## 回滚方式

计划文件回滚：
- 恢复 `implementation_plan.md` 到修改前版本。

后续实施回滚建议：
- 回退 `apps/web/app/api/[...path]/route.ts` 的 proxy route。
- 回退 `apps/web/lib/constants.ts` 的 API base 调整。
- 回退 `apps/web/lib/api.ts` 的同源 URL 构造调整。
- 回退 `apps/web/lib/query.ts` 及调用点。
- 回退 `SignalFilters.tsx` 的平台 select 改动。
- 回退 `AppShell.tsx` 的 backend status 展示。

