# SignalForge Frontend Round 1 Change Report

## PASS/FAIL

PASS

## 任务判断

- Next route handler runtime proxy、浏览器同源 `/api`、`/api/health -> /health`、Product Hunt 平台值、query 保留、导航/项目选择/机会详情 query 保留、AppShell 真实后端状态均已复核。
- 未接入真实 X/Discord/LLM/embedding，未新增正式认证系统。
- 未发现阻塞项，未生成 `blocking_issue.md`。

## 修改文件清单

- `apps/web/app/api/[...path]/route.ts`
- `apps/web/lib/api.ts`
- `apps/web/lib/constants.ts`
- `apps/web/lib/query.ts`
- `apps/web/components/signals/SignalFilters.tsx`
- `apps/web/components/layout/Navigation.tsx`
- `apps/web/components/layout/ProjectSelector.tsx`
- `apps/web/components/layout/AppShell.tsx`
- `apps/web/components/opportunities/OpportunityCard.tsx`
- `apps/web/components/opportunities/OpportunityDetail.tsx`
- `frontend_change_report.md`

## 已复核未改

- `apps/web/app/opportunities/[id]/page.tsx`

## 改动目的

- 通过 `apps/web/app/api/[...path]/route.ts` 提供 Node.js runtime 同源代理，浏览器请求 `/api/*` 经 Next 转发到 FastAPI。
- 浏览器默认使用同源 `/api`，服务端渲染默认使用 `SERVER_API_BASE_URL`。
- `/api/health` 映射到 FastAPI `/health`，其他 `/api/*` 保持后端 `/api/*` 路径。
- query helper 仅保留 `projectId` 与 `sf_token`，并用于导航、项目选择、机会卡片与机会详情返回链接。
- 信号平台筛选改为 select，Product Hunt value 固定为 `product_hunt`。
- AppShell 使用 `api.health()` 与项目列表请求共同判断后端连接状态。

## 执行命令

- `python3 scripts/validate_frontend_mvp.py`
- `npx tsc --noEmit --incremental false`，工作目录 `apps/web`
- `npm run build`，工作目录 `apps/web`
- `curl -i -sS 'http://localhost:3000/api/health?sf_token=frontend-smoke' | sed -n '1,30p'`
- `curl -i -sS 'http://localhost:3000/opportunities?projectId=frontend-smoke&sf_token=frontend-smoke' | sed -n '1,20p'`
- `curl -sS 'http://localhost:3000/api/projects?page_size=3&sf_token=frontend-smoke' | head -c 2000`

## 验证结果

- PASS: `python3 scripts/validate_frontend_mvp.py`
- PASS: `npx tsc --noEmit --incremental false`
- PASS: `npm run build`
- PASS: `GET /api/health?sf_token=frontend-smoke` 返回 HTTP 200，响应来自 FastAPI `/health`。
- PASS: 机会页 HTML 中导航链接保留 `projectId` 与 `sf_token`。
- PASS: `GET /api/projects?page_size=3&sf_token=frontend-smoke` 返回 HTTP 200，确认同源 `/api` 代理可访问后端项目接口。

## 残留问题

- 使用伪造 `projectId=frontend-smoke` 请求机会页时，后端返回 422 校验错误；这是测试输入无效导致，不是前端阻塞。
- 当前本机项目样例中未找到可用于截图验证的机会卡片数据，机会卡片 query 保留通过代码路径、TypeScript 和构建验证覆盖。
- 工作树存在其他 agent 的后端、脚本和文档改动，本轮未回滚、未覆盖。

## 回滚方式

- 回滚本轮已跟踪文件改动：`git restore -- apps/web/components/opportunities/OpportunityCard.tsx apps/web/components/opportunities/OpportunityDetail.tsx`
- 若需要回滚整个 Frontend Round 1 已跟踪边界：`git restore -- apps/web/components/layout/AppShell.tsx apps/web/components/layout/Navigation.tsx apps/web/components/layout/ProjectSelector.tsx apps/web/components/opportunities/OpportunityCard.tsx apps/web/components/opportunities/OpportunityDetail.tsx apps/web/components/signals/SignalFilters.tsx apps/web/lib/api.ts apps/web/lib/constants.ts`
- 对未跟踪新增文件，需经审批后移除：`apps/web/app/api/[...path]/route.ts`、`apps/web/lib/query.ts`、`frontend_change_report.md`。

---

# SignalForge Frontend Personal Production v1 Workflow Review

## PASS/FAIL

PASS

## 修改文件清单

- `apps/web/components/layout/ProjectSelector.tsx`
- `apps/web/components/settings/SettingsPage.tsx`
- `apps/web/components/signals/SignalDetailPreview.tsx`
- `apps/web/components/opportunities/OpportunitiesPage.tsx`
- `apps/web/app/opportunities/page.tsx`
- `apps/web/e2e/personal-workflow.spec.ts`
- `frontend_change_report.md`

## 改动目的

- 防止 `/onboarding` 被项目选择器自动追加已有 `projectId`，保证新建项目工作流可提交后进入 Dashboard。
- 设置页仅展示环境配置数量和状态，不渲染具体 env 名称或后端返回的敏感标记。
- 信号详情预览展示 `source_url`，满足来源可追溯。
- 机会看板改为客户端加载，确保 Playwright 浏览器 API mock 能覆盖完整 UI workflow。
- E2E 断言改为唯一定位，避免文本重复导致 strict mode 失败。

## 执行命令

- `npx tsc --noEmit --incremental false`，工作目录 `apps/web`
- `npm run test:e2e -- --project=chromium`，工作目录 `apps/web`
- `npm run build`，工作目录 `apps/web`
- `rg -n "PRODUCT_HUNT_TOKEN|REDDIT_CLIENT_SECRET|encrypted_payload" apps/web/app apps/web/components apps/web/lib -g '!node_modules/**' -g '!.next/**'`

## 验证结果

- PASS: TypeScript no-emit 检查通过。
- PASS: Playwright `personal-workflow.spec.ts` 通过，覆盖 onboarding、settings、logs、dashboard controls、signals、opportunities、reports Markdown/CSV 导出和敏感标记不可见断言。
- PASS: `npm run build` 通过。
- PASS: 前端 app/components/lib 源码未检出 `PRODUCT_HUNT_TOKEN`、`REDDIT_CLIENT_SECRET`、`encrypted_payload`。

## 残留问题

- 工作树仍存在其他 agent 的 API、脚本、文档和部分 frontend 既有改动，本轮未回滚、未覆盖。
- `apps/web/e2e/personal-workflow.spec.ts` 当前为未跟踪文件；本轮只在该文件内调整了断言。

## 回滚方式

- 回滚本轮已跟踪文件改动：`git restore -- apps/web/components/layout/ProjectSelector.tsx apps/web/components/settings/SettingsPage.tsx apps/web/components/signals/SignalDetailPreview.tsx apps/web/app/opportunities/page.tsx frontend_change_report.md`
- 未跟踪新增文件需经审批后移除：`apps/web/components/opportunities/OpportunitiesPage.tsx`。
- 若需要回退本轮对未跟踪 E2E 文件的调整，请恢复 `apps/web/e2e/personal-workflow.spec.ts` 中信号标题、CSV 标题和 CSV 内容定位断言。
