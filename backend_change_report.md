# Backend Change Report

## PASS/FAIL

PASS

## 任务判断

- 任务：实现 env-status Settings API，并复核 mock collection/processing/report 链路是否已满足稳定 raw_items/signals/opportunity/report 要求。
- 结论：已完成。新增端点只读取 `os.environ`，不读取或写入 `PlatformCredential.encrypted_payload`，不实现 credential CRUD，不做真实外部平台验证。
- 链路复核结论：现有 mock collection、processing、signals、opportunities、reports 相关测试通过，无需修改 backend report service。

## 当前目标

- 新增 `POST /api/settings/platforms/{platform}/test`。
- 响应字段包含：`platform`、`status`、`message`、`checked_at`、`required_env_missing`。
- 支持状态枚举：`available`、`missing_env`、`configured_unverified`、`valid`、`invalid`、`rate_limited`、`permission_limited`、`coming_soon`。
- 保证响应 secret-safe：返回缺失 env 名称，不返回 env 值、Bearer header 或 token payload。

## 已确认事实

- `reddit` 必需 env：`REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET`、`REDDIT_USER_AGENT`。
- `product_hunt` 必需 env：`PRODUCT_HUNT_TOKEN`。
- `x`、`discord` 当前不是 MVP 可用平台，测试端点返回 `coming_soon`。
- P0 平台 env 完整时返回 `configured_unverified`，因为该端点按要求只读本地 env，不做 live platform verification。
- 全量 API 测试通过：`127 passed in 1.07s`。
- 最终工作区存在多项非本轮后端改动，包括 `apps/web/*`、若干报告文件和未跟踪文档；本轮未回滚、未编辑这些非所有权文件。

## 风险点

- `required_env_missing` 会暴露缺失环境变量名称；这是接口要求字段，不暴露变量值。
- `configured_unverified` 只证明进程环境变量存在且非空，不证明凭据有效、权限足够或未被限流。
- 宿主机 Python 缺少 pytest；有效验证使用 Docker API 容器。
- Docker Compose build 仍输出 buildx 插件 warning，但 API 镜像构建成功。

## 推荐方案

- 保持当前最小实现：env-only readiness/status endpoint。
- 如后续需要 `valid`、`invalid`、`rate_limited`、`permission_limited`，应另行审批 live smoke test 或平台验证策略。
- 不新增加密、密钥配置、数据库迁移或 credential CRUD。

## 改动边界

- 已修改 settings route/schema/service 和 settings API 测试。
- 未修改数据库模型、迁移、凭据表写入逻辑、连接器真实请求逻辑。
- 未修改 report service；测试显示现有报告链路满足当前稳定性要求。

## 修改文件清单

- `apps/api/app/api/routes/settings.py`
- `apps/api/app/schemas/settings.py`
- `apps/api/app/services/settings.py`
- `apps/api/tests/test_settings_api.py`
- `backend_change_report.md`

## 改动目的

- `routes/settings.py`：新增 `POST /api/settings/platforms/{platform}/test` endpoint，并对未知平台返回标准 not_found error envelope。
- `schemas/settings.py`：新增 `PlatformTestStatus` 与 `PlatformEnvTestResponse`。
- `services/settings.py`：新增 env-only 平台状态判断、平台别名归一化、必需 env 缺失计算。
- `tests/test_settings_api.py`：覆盖 missing_env、configured_unverified secret-safe、coming_soon、unsupported platform。
- `backend_change_report.md`：记录本轮实施、验证、残留问题与回滚方式。

## 执行命令

1. `git status --short`
   - 结果：PASS
   - 初始发现：存在未跟踪文件 `current_state_report.md`、`token_behavior_report.md`，本轮未修改。

2. `rg --files apps/api`
   - 结果：PASS
   - 用途：确认后端文件结构。

3. `rg -n "settings|PlatformCredential|report|raw_items|signals|opportunity|test" apps/api -S`
   - 结果：PASS
   - 用途：定位 settings、凭据、报告和数据链路相关代码。

4. `python3 -m pytest apps/api/tests/test_settings_api.py`
   - 结果：FAIL_TO_RUN
   - 说明：宿主机 Python 缺少 pytest。

5. `docker compose -f infra/docker-compose.yml build api`
   - 结果：PASS_WITH_WARNING
   - 说明：API 镜像构建成功；Compose 输出 buildx 插件 warning。

6. `docker compose -f infra/docker-compose.yml run --rm api pytest tests/test_settings_api.py`
   - 结果：PASS
   - 输出：`6 passed in 0.44s`

7. `docker compose -f infra/docker-compose.yml run --rm api pytest tests/test_mock_connector.py tests/test_collection_executor.py tests/test_collection_api.py tests/test_processing_pipeline.py tests/test_signals_api.py tests/test_opportunities_api.py tests/test_reports_api.py`
   - 结果：PASS
   - 输出：`25 passed in 0.74s`

8. `docker compose -f infra/docker-compose.yml run --rm api pytest`
   - 结果：PASS
   - 输出：`127 passed in 1.07s`

9. `git status --short`
   - 结果：PASS
   - 最终发现：除本轮后端文件外，工作区还有前端、报告和未跟踪文档改动；按并行协作约束保留不动。

## 验证结果

- Settings env-status API 专项测试通过。
- 相关 mock collection/processing/signals/opportunities/reports 测试通过。
- 全量 API 测试通过。
- 未发现需要修改 `apps/api/app/services/reports.py` 的缺口。

## 残留问题

- 当前端点不验证真实凭据有效性；这是 env-only 需求的预期限制。
- 宿主机 pytest 不可用；后续本地快速验证仍需 Docker 或安装测试依赖。
- 工作区存在非本轮后端改动和未跟踪文件，本轮未处理。

## 回滚方式

- 删除 `apps/api/app/api/routes/settings.py` 中 `test_platform_env_status` endpoint 和 `not_found`、`PlatformEnvTestResponse` import。
- 删除 `apps/api/app/schemas/settings.py` 中 `PlatformTestStatus`、`PlatformEnvTestResponse` 和 `Field` import。
- 删除 `apps/api/app/services/settings.py` 中 env-status 相关 import、`REQUIRED_ENV_BY_PLATFORM`、`PLATFORM_ALIASES`、`test_platform_env_status`、`normalize_platform_name`。
- 删除 `apps/api/tests/test_settings_api.py` 中新增 4 个 env-status 测试及 connector env constants import。
- 将 `backend_change_report.md` 恢复为本轮修改前版本。

## Backend Agent Validation Addendum - 2026-04-30

### PASS/FAIL

PASS

### 本轮确认事实

- Compose API 服务不挂载 `apps/api` 源码，验证本地后端改动前必须重新 build `infra-api` 镜像。
- 重建镜像后，reports 输出包含 `source_url`、`recommended_action`、`mode`，抽样未发现 `encrypted_payload` 或 `token`。
- mock connector 当前返回 5 条稳定 mock raw_items，旧 collection 测试仍硬编码 3 条，已更新为 5 条。

### 本轮追加修改文件

- `apps/api/tests/test_collection_executor.py`
- `apps/api/tests/test_collection_api.py`
- `backend_change_report.md`

### 本轮追加验证

1. `python3 -m pytest apps/api/tests/test_settings_api.py apps/api/tests/test_mock_connector.py apps/api/tests/test_reports_api.py`
   - 结果：FAIL_TO_RUN
   - 说明：宿主机 Python 缺少 pytest。

2. `docker compose -f infra/docker-compose.yml build api`
   - 结果：PASS_WITH_WARNING
   - 说明：API 镜像构建成功；Compose 输出 buildx 插件 warning。

3. `docker compose -f infra/docker-compose.yml run --rm api pytest tests/test_settings_api.py tests/test_mock_connector.py tests/test_reports_api.py`
   - 结果：PASS
   - 输出：`10 passed in 0.56s`

4. `docker compose -f infra/docker-compose.yml run --rm api pytest tests/test_collection_executor.py tests/test_collection_api.py tests/test_processing_pipeline.py tests/test_signals_api.py tests/test_opportunities_api.py tests/test_reports_api.py`
   - 结果：PASS
   - 输出：`24 passed in 0.89s`

### 本轮回滚方式

- 将 `apps/api/tests/test_collection_executor.py` 中 `EXPECTED_MOCK_ITEMS = 5` 相关断言恢复为旧值 `3`。
- 将 `apps/api/tests/test_collection_api.py` 中 `EXPECTED_MOCK_ITEMS = 5` 相关断言恢复为旧值 `3`，并恢复 `raw_item_count(project_id) > before_count`。
- 删除本 addendum。
