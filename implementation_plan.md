# SignalForge Round 1 Implementation Plan

## 任务判断

结论：Round 1 目标是修复外部访问场景下前端无法稳定访问后端的问题，并将信号收件箱的平台筛选从自由文本升级为受控的平台选项。实施范围应限制在前端同源代理、前端 API client 调整和筛选 UI/参数构造，不涉及数据模型、迁移、后端业务 API 或真实外部平台调用。

依据：
- 当前前端 API client 通过 `NEXT_PUBLIC_API_BASE_URL` 构造后端绝对地址；外部访问部署时容易暴露 `localhost`、内网地址或跨域限制。
- 当前信号筛选组件的平台筛选是文本输入，已存在后端 `platform` 查询参数，可复用现有业务 API。
- 已批准 PRD 明确为“外部可访问修复与平台筛选升级”。

## 当前目标

1. 外部可访问修复：前端浏览器请求改为访问同源路径，由 Next.js 前端侧 proxy 转发到既有后端。
2. 平台筛选升级：信号收件箱平台筛选改为明确的平台选项，避免自由文本输入造成的无效筛选。
3. 保持后端业务接口、数据结构和迁移不变。
4. 保持 token、密钥和真实外部平台 API 不写入、不调用。

## 已确认事实

- `apps/web/lib/constants.ts` 当前定义 `DEFAULT_API_BASE_URL = "http://localhost:8000"`，并读取 `NEXT_PUBLIC_API_BASE_URL`。
- `apps/web/lib/api.ts` 当前通过 `new URL(normalizedPath, API_BASE_URL)` 生成后端请求 URL。
- `apps/web/components/signals/SignalFilters.tsx` 当前平台筛选为文本输入。
- `apps/web/components/signals/SignalInbox.tsx` 当前会将 `filters.platform.trim()` 映射为 `SignalListParams.platform`。
- `apps/web/lib/types.ts` 已定义 `PlatformName = "reddit" | "product_hunt" | "x" | "discord"`。
- 后端已有 `GET /api/projects/{project_id}/signals`，支持 `platform` 查询参数；Round 1 不需要新增后端业务 API。

## 功能模块拆分

### 模块 1：前端同源 Proxy

目标：让浏览器只请求 Web 同源 `/api/*` 路径，由 Next.js 侧转发到后端服务。

建议改动：
- 在 Next.js 配置或前端运行层新增同源 proxy 规则。
- proxy 目标使用服务端环境变量，例如 `API_BASE_URL` 或保留既有后端地址变量的服务端版本。
- 前端公开变量不再要求暴露后端绝对地址。
- 保留请求超时、错误解析和 JSON envelope 处理逻辑。

边界：
- 不新增后端业务 API。
- 不改变 FastAPI route、schema、service。
- 不写入 token、密钥或真实平台凭据。

### 模块 2：前端 API Client 调整

目标：让前端 API client 默认请求同源 `/api/*`，并继续禁止传入任意外部 URL。

建议改动：
- 将 API base 默认值从浏览器可见的后端绝对地址调整为同源空前缀或 `/`。
- `buildBackendUrl` 继续只接受相对路径。
- 生产和本地都通过同源路径访问，proxy 决定实际后端地址。
- 错误信息可继续使用 “SignalForge backend” 表述，无需改业务语义。

边界：
- 不改变 API response 类型。
- 不改变分页、筛选、状态更新、处理运行等业务调用路径。

### 模块 3：平台筛选控件升级

目标：将平台筛选从文本输入改为受控选项，降低无效输入和大小写不一致风险。

建议改动：
- `SignalFilters` 中平台筛选改为 `<select>`。
- 选项包含“全部平台”、`reddit`、`product_hunt`、`x`、`discord`。
- 选项值必须与后端已有 `RawItem.platform`/前端 `PlatformName` 保持一致。
- `SignalInbox.buildSignalListParams` 继续将空值映射为 `undefined`，非空值传给 `platform`。

边界：
- 不新增平台。
- 不修改后端筛选语义。
- 不修改数据展示字段。

### 模块 4：验证与回滚

目标：通过本地静态检查和最小手动验证确认改动有效、可回滚。

建议验证：
- 前端 TypeScript/构建检查通过。
- 本地 Web 页面请求路径为同源 `/api/*`。
- 平台筛选选择 `reddit`、`product_hunt`、`x`、`discord` 时，请求 query 中平台值准确。
- 清空平台筛选时不发送 `platform` query。
- 后端测试无需因本轮改动新增 migration 或业务 API 测试。

## 数据结构变化

无。

说明：
- 不修改数据库表。
- 不新增 Alembic migration。
- 不修改 Pydantic schema 的字段定义。
- 不修改前后端业务实体结构。

## API 变化

新增前端同源 proxy，不新增后端业务 API。

说明：
- 浏览器访问路径变化为 Web 同源 `/api/*`。
- Next.js 前端层负责将 `/api/*` 转发到既有 FastAPI 后端。
- FastAPI 现有业务 API 路径、请求参数、响应结构不变。
- 不新增、删除或重命名后端业务 endpoint。

## 前端改动点

1. `apps/web/next.config.mjs`
   - 增加同源 proxy/rewrite 配置。
   - 目标后端地址从服务端环境变量读取。

2. `apps/web/lib/constants.ts`
   - 调整 API base 策略，默认使用同源路径。
   - 避免生产浏览器依赖 `localhost:8000`。

3. `apps/web/lib/api.ts`
   - 保持仅允许相对路径。
   - 确保 `/api/*` 请求能在同源模式下正确构造。

4. `apps/web/components/signals/SignalFilters.tsx`
   - 将平台输入框替换为平台下拉选择。
   - 保持 disabled、reset 和 `onChange` 行为一致。

5. `apps/web/components/signals/SignalInbox.tsx`
   - 保持筛选参数构造逻辑。
   - 必要时收紧 `platform` 类型，但不改变接口语义。

## 风险点

### P0

- Proxy 路径循环或目标错误，导致所有 `/api/*` 请求不可用。
- 生产环境未配置服务端后端地址，外部访问仍转发到不可达地址。
- 同源 proxy 误转发 Next.js 自身 route，造成前端页面或静态资源异常。

### P1

- 平台选项值与后端实际存储值不一致，导致筛选结果为空。
- 本地开发与部署环境变量命名不一致，造成环境可用性偏差。
- API client URL 拼接处理不当，导致 query 参数丢失或双斜杠路径异常。

### P2

- 平台筛选下拉文案不够清晰，用户难以区分 `product_hunt` 等技术值。
- 只做前端筛选控件升级，不解决历史数据中可能存在的非标准平台值。
- 错误提示仍使用通用 backend 文案，无法直接提示 proxy 配置问题。

## 不做事项

- 不执行 `git add`、`git commit`、`git reset`、`git revert`。
- 不修改应用代码，本文件仅作为实施计划交付。
- 不新增 migration。
- 不修改数据库结构或数据。
- 不新增后端业务 API。
- 不调用真实 Reddit、Product Hunt、X、Discord 或其他外部平台 API。
- 不写入 token、密钥、凭据或权限配置。
- 不做批量重构。
- 不改变信号处理、采集、评分、聚类、机会生成等生产逻辑。

## Subagent 工作流边界

### PM / Requirement Agent

职责：
- 将已批准 PRD 转化为最小可执行实施计划。
- 明确目标、范围、风险、验收标准和不做事项。
- 不改应用代码。
- 不执行 git 暂存、提交、回滚。

交付物：
- `implementation_plan.md`

### Frontend Agent

职责：
- 在批准后实现 Next.js 同源 proxy。
- 调整前端 API client 的同源请求策略。
- 将平台筛选 UI 从文本输入改为受控下拉。
- 执行前端类型检查/构建验证。

禁止：
- 修改后端业务逻辑。
- 写入密钥或调用真实外部平台。
- 新增 migration。

### Backend Agent

职责：
- 默认不参与代码改动。
- 仅在验证发现现有 API 与 PRD 不一致时，提供事实确认和最小修复建议。

禁止：
- 新增业务 API。
- 修改数据结构。
- 新增 migration。
- 调用真实外部平台 API。

### QA / Verification Agent

职责：
- 验证同源 `/api/*` 请求路径。
- 验证平台筛选 query 参数。
- 验证“全部平台”不发送 `platform` 参数。
- 验证前端构建或类型检查。

禁止：
- 使用真实外部平台 API。
- 写入 token 或修改生产配置。

## 实施步骤

1. 获取审批：确认 Round 1 进入实现阶段，并确认允许修改前端代码。
2. 实现前端同源 proxy：在 Next.js 层配置 `/api/*` 到后端目标的转发。
3. 调整 API client：默认请求同源 `/api/*`，保留相对路径限制。
4. 升级平台筛选：将平台文本框替换为下拉选择。
5. 本地验证：运行前端类型检查/构建，启动本地 Web 和 API，验证请求路径与筛选行为。
6. 输出实施报告：列出修改文件、命令、验证结果、残留风险和回滚方式。

## 验证标准

- 浏览器 Network 中业务请求为同源 `/api/*`。
- `/api/*` 能成功转发到既有 FastAPI 后端。
- 信号收件箱选择平台后，请求 query 包含对应 `platform` 值。
- 选择“全部平台”后，请求 query 不包含 `platform`。
- 前端类型检查或构建通过。
- 未出现数据库 migration 文件。
- 未出现后端业务 API 新增。
- 未写入 token、密钥或真实平台凭据。
- 未调用真实外部平台 API。

## 回滚方式

计划阶段回滚：
- 删除 `implementation_plan.md` 或恢复到修改前状态。

后续实现阶段建议回滚：
- 回退 `apps/web/next.config.mjs` 中的 proxy/rewrite 配置。
- 回退 `apps/web/lib/constants.ts` 与 `apps/web/lib/api.ts` 的同源请求调整。
- 回退 `apps/web/components/signals/SignalFilters.tsx` 的平台下拉改动。
- 若 `SignalInbox.tsx` 仅有类型收紧或参数构造微调，同步回退该文件。

