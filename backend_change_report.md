# Backend Change Report

## PASS/FAIL

PASS

## 任务判断

- 任务：复核并补齐 CORS env parser 与 FastAPI CORS 配置，新增或修正 parser 测试。
- 结论：已完成。未发现需要写入 `blocking_issue.md` 的阻塞问题。

## 当前目标

- 保持 CORS 默认只允许本地前端来源。
- 允许通过 `CORS_ALLOW_ORIGINS` 以逗号分隔形式覆盖来源。
- 防止空 env 值把允许来源解析为空集合。
- 确认 FastAPI `CORSMiddleware` 使用统一 settings 配置。

## 已确认事实

- `apps/api/app/main.py` 已通过 `app_settings.cors_allow_origins` 配置 `CORSMiddleware.allow_origins`。
- `apps/api/app/config.py` 已定义默认来源：
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- parser 会执行逗号分割、空白裁剪、尾部 `/` 清理、空项过滤。
- 本轮补齐：当 env 值为空或只包含空项时，parser 回退默认来源。
- 未修改数据库 schema。
- 未新增 migration。
- 未接入真实外部平台。
- 未执行 `git add`、`git commit`、`git reset`、`git revert`。

## 修改文件清单

- `apps/api/app/config.py`：本轮写入。
- `apps/api/app/main.py`：工作区已有 CORS settings 接线改动；本轮复核，未继续编辑。
- `apps/api/tests/test_cors_config.py`：本轮写入。
- `backend_change_report.md`：本轮写入。

## 改动目的

- `apps/api/app/config.py`：让 `parse_cors_allow_origins` 在解析结果为空时返回 `DEFAULT_CORS_ALLOW_ORIGINS`，避免空字符串或全空逗号列表导致 CORS 来源被清空。
- `apps/api/app/main.py`：确认 FastAPI `CORSMiddleware` 通过 `app_settings.cors_allow_origins` 读取统一配置，而不是写死 origin 列表。
- `apps/api/tests/test_cors_config.py`：新增空 env 值回退默认来源的 parser 测试，并保留默认值、空白裁剪、空项过滤、尾斜杠清理、FastAPI 中间件配置测试。
- `backend_change_report.md`：记录本轮实施、验证、残留问题与回滚方式。

## 改动边界

- 仅写入任务指定边界内文件。
- 未修改 `infra/docker-compose.yml`、数据库模型、迁移文件、前端文件或外部平台连接逻辑。
- `apps/api/app/main.py` 已满足目标，本轮未继续扩大改动。

## 执行命令

1. `pwd && git status --short`
   - 结果：PASS
   - 用途：确认工作目录和现有未提交改动。

2. `rg -n "CORS|cors|ALLOWED|allowed|origins|ORIGINS|BaseSettings|Settings" apps/api/app apps/api/tests pyproject.toml pytest.ini setup.cfg`
   - 结果：FAIL_PARTIAL_WITH_USEFUL_OUTPUT
   - 用途：定位 CORS 与 settings 相关代码。
   - 说明：命令定位到目标代码；同时因为根目录不存在 `pyproject.toml`、`pytest.ini`、`setup.cfg`，`rg` 返回非零状态。

3. `sed -n '1,240p' apps/api/app/config.py`
   - 结果：PASS
   - 用途：复核 parser 与 settings。

4. `sed -n '1,240p' apps/api/app/main.py`
   - 结果：PASS
   - 用途：复核 FastAPI CORS 中间件配置。

5. `sed -n '1,240p' apps/api/tests/test_cors_config.py`
   - 结果：PASS
   - 用途：复核已有 CORS 测试。

6. `rg -n "CORS_ALLOW_ORIGINS|cors|CORS" .env.example README.md apps/api/README.md infra/docker-compose.yml docs scripts`
   - 结果：PASS
   - 用途：确认环境变量使用位置。

7. `python -m pytest apps/api/tests/test_cors_config.py`
   - 结果：FAIL_TO_RUN
   - 说明：宿主机无 `python` 命令。

8. `python3 -m pytest apps/api/tests/test_cors_config.py`
   - 结果：FAIL_TO_RUN
   - 说明：宿主机 `python3` 未安装 `pytest`。

9. `docker compose -f infra/docker-compose.yml build api`
   - 结果：PASS_WITH_WARNING
   - 说明：API 镜像构建成功；Docker Compose 输出 `Docker Compose requires buildx plugin to be installed` warning，但未阻塞构建。

10. `docker compose -f infra/docker-compose.yml run --rm api pytest tests/test_cors_config.py`
    - 结果：PASS
    - 说明：容器内 API rootdir 为 `/app`，测试路径使用 `tests/test_cors_config.py`。

## 验证结果

- Docker API 容器专项测试通过。
- 测试输出：`4 passed in 0.40s`。
- 覆盖项：
  - `None` env 值返回默认 CORS 来源。
  - 空字符串/全空项 env 值返回默认 CORS 来源。
  - 逗号分隔 env 值会裁剪空白、过滤空项、移除尾部 `/`。
  - FastAPI `CORSMiddleware.allow_origins` 与 `settings.cors_allow_origins` 一致。
  - 默认中间件配置不包含 `*` wildcard。

## 风险点

- 宿主机 Python 环境缺少可直接运行 pytest 的依赖；当前有效验证依赖 Docker API 镜像。
- Docker Compose 构建仍输出 buildx 插件 warning；本轮未修改 Docker 工具链配置。
- 当前 parser 不做 URL 语义校验，只做本任务范围内的分隔、清理与回退。

## 残留问题

- 无 CORS parser 或 FastAPI CORS 配置相关阻塞问题。
- 未执行全量 API 测试；本轮只按任务目标执行 CORS 专项测试。

## 回滚方式

- 回滚 `apps/api/app/config.py` 中 `return tuple(origins) or DEFAULT_CORS_ALLOW_ORIGINS` 为 `return tuple(origins)`。
- 如需回滚工作区已有 FastAPI CORS 接线改动，将 `apps/api/app/main.py` 的 `allow_origins=app_settings.cors_allow_origins` 恢复为原写死列表，并移除对应 `app.config` import。
- 删除 `apps/api/tests/test_cors_config.py` 中 `test_cors_allow_origins_parser_empty_value_uses_default` 测试。
- 将 `backend_change_report.md` 恢复到本轮修改前内容。
