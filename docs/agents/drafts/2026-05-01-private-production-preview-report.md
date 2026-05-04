# SignalForge 本机私有生产真实接口预览报告

日期：2026-05-01
分支：`feature/personal-production-v1`
执行模式：subagent 分片执行
目标形态：Mac mini 本机私有生产预览
访问边界：计划为仅本机访问；本轮发现已有公网 tunnel 进程，见 No-Go 项

## 任务判断

本轮结论：**NO-GO**。

原因：

- local/mock 回归门禁全 PASS，说明现有本地业务链路未退化。
- 真实 Reddit、Product Hunt、LLM、Embedding 预览均未真正执行，因为当前 shell 环境中真实 smoke 开关和凭据全部未设置。
- 安全证据分片发现已有 `cloudflared tunnel --url http://localhost:3000` 进程，和“仅本机访问、不公网暴露”的生产边界冲突。
- 未发现 token/secret 泄露，`validate_no_secrets.py` PASS。
- 本轮没有设置 `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true`，没有真实平台写库。

## 当前目标

用 subagent 模式验证 SignalForge 是否可进入本机私有生产预览：

1. 启动本机 Docker Compose 服务。
2. 跑 local/mock 回归门禁。
3. 在 local/mock 全 PASS 后运行真实平台和真实模型 preview smoke。
4. 不写 `raw_items`，不启用公网，不打印或保存密钥。
5. 输出 Go/No-Go 和后续执行路径。

## 已确认事实

- 初始工作树非 clean。
- 初始真实接口相关 env 均为 `UNSET`。
- Docker Compose 服务由主线程启动，local/mock 回归后已停止。
- local/mock 回归全 PASS。
- 真实平台脚本返回门禁状态，未发起真实平台调用。
- 真实 LLM/Embedding 脚本返回门禁状态，未发起 provider call。
- `validate_no_secrets.py` PASS。
- `pgrep` 发现已有 `cloudflared` tunnel 进程。
- 本轮没有推送、没有提交、没有改配置、没有启用真实写库、没有启动新的 tunnel。

## 执行命令

### Env Gate Agent

| 命令 | 结果 | 退出码 | 关键输出 |
|---|---:|---:|---|
| `git status --short --branch` | PASS | 0 | 当前分支 `feature/personal-production-v1`；工作树非 clean |
| `docker compose -f infra/docker-compose.yml ps` | PASS | 0 | 初始无运行中的 Compose 服务 |
| env SET/UNSET 检查 | PASS | 0 | 真实平台、真实 LLM、真实 embedding 相关变量均为 `UNSET` |

初始 env 事实：

```text
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=UNSET
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=UNSET
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=UNSET
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=UNSET
REDDIT_CLIENT_ID=UNSET
REDDIT_CLIENT_SECRET=UNSET
REDDIT_USER_AGENT=UNSET
PRODUCT_HUNT_TOKEN=UNSET
LLM_API_KEY=UNSET
OPENAI_API_KEY=UNSET
ANTHROPIC_API_KEY=UNSET
EMBEDDING_API_KEY=UNSET
LLM_BASE_URL=UNSET
LLM_MODEL=UNSET
EMBEDDING_MODEL=UNSET
```

### Orchestrator

| 命令 | 结果 | 退出码 | 关键输出 |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml up -d` | PASS | 0 | API/Web/Postgres/Redis 启动，Postgres/Redis healthy |

### Local Regression Agent

| 命令 | 结果 | 退出码 | 关键输出 |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml ps` | PASS | 0 | api/web/postgres/redis 均 Up |
| `python3 scripts/wait_for_services.py` | PASS | 0 | postgres、redis、api `/health`、web `/` ready |
| `docker compose -f infra/docker-compose.yml run --rm api alembic upgrade head` | PASS | 0 | Alembic PostgreSQL migration context 正常 |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/seed_demo_data.py` | PASS | 0 | `PASS: demo data seeded` |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_data_model.py` | PASS | 0 | demo project、raw_items、signals、clusters、opportunities 通过 |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_backend_api.py` | PASS | 0 | API、reports、settings、collect 全通过；无 token 泄漏 |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_connector_abstraction.py` | PASS | 0 | connector contract、mock/disabled connector、collection logs/idempotency 通过 |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_p0_connectors.py --no-token-leak` | PASS | 0 | P0 connectors 安全降级、mock reddit/product_hunt、no-token-leak 通过 |
| `docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/validate_processing_pipeline.py` | PASS | 0 | `raw_items -> signals -> embeddings -> clusters -> opportunities` 通过 |
| `docker compose -f infra/docker-compose.yml run --rm api pytest` | PASS | 0 | `128 passed in 0.92s` |
| `docker compose -f infra/docker-compose.yml run --rm web npm run build` | PASS | 0 | Next.js production build 通过，10 个 static pages |
| `python3 scripts/validate_frontend_mvp.py --require-http` | PASS | 0 | Phase 6 pages、source links、高价值标记、reports export、HTTP smoke 通过 |
| `API_BASE_URL=http://localhost:8000 python3 scripts/validate_personal_workflow.py` | PASS | 0 | project/keywords/mock collection/processing/signals/opportunities/reports/cleanup 通过 |

### Real Platform Preview Agent

| 脚本 | 状态 | 退出码 | 关键输出 | 是否写库 |
|---|---:|---:|---|---|
| `manual_reddit_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `write_enabled: False` | 否 |
| `manual_product_hunt_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `write_enabled: False` | 否 |

说明：subagent 原始状态口径把门禁未开启归类为 `PERMISSION_LIMITED`，本报告按脚本输出和实际行为统一归类为 `NOT_EXECUTED`，因为没有真实平台调用。

### Real Model Preview Agent

| 脚本 | 状态 | 退出码 | 关键输出 | Provider call |
|---|---:|---:|---|---|
| `manual_llm_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `real_provider_called: False` | 否 |
| `manual_embedding_smoke.py` | NOT_EXECUTED | 0 | `DISABLED_MISSING_TOKEN`; `No provider call was made.` | 否 |

### Security Evidence Agent

| 命令 | 结果 | 退出码 | 关键输出 |
|---|---:|---:|---|
| `python3 scripts/validate_no_secrets.py` | PASS | 0 | `PASS: no secrets validation` |
| `docker compose -f infra/docker-compose.yml ps` | PASS | 0 | 执行时 Compose 服务正在运行，端口绑定 `0.0.0.0` |
| `pgrep -fl 'cloudflared|trycloudflare' || true` | FAIL_BLOCKER | 0 | 发现 `cloudflared tunnel --url http://localhost:3000` |
| `git status --short --branch` | PASS_WITH_RISK | 0 | 工作树非 clean |

发现的 tunnel 进程：

```text
SCREEN -dmS signalforge_tunnel ... cloudflared tunnel ... --url http://localhost:3000
cloudflared tunnel --metrics 127.0.0.1:0 --url http://localhost:3000
```

### Cleanup

| 命令 | 结果 | 退出码 | 关键输出 |
|---|---:|---:|---|
| `docker compose -f infra/docker-compose.yml down` | PASS | 0 | API/Web/Postgres/Redis 容器和网络已移除 |
| `docker compose -f infra/docker-compose.yml ps` | PASS | 0 | 无运行中的 Compose 服务 |
| `pgrep -fl 'cloudflared|trycloudflare' || true` | FAIL_BLOCKER | 0 | tunnel 进程仍存在；本轮未擅自停止 |

## PASS / FAIL / NOT_EXECUTED 矩阵

| 区域 | 状态 | 证据 |
|---|---:|---|
| 本机 Compose 启动 | PASS | `docker compose up -d` 成功 |
| local/mock 回归 | PASS | 13 个 local/mock 命令全 PASS |
| API pytest | PASS | `128 passed in 0.92s` |
| Frontend build/HTTP smoke | PASS | build 和 `validate_frontend_mvp.py --require-http` 通过 |
| Personal workflow E2E | PASS | `validate_personal_workflow.py` 通过 |
| no-secrets 检查 | PASS | `validate_no_secrets.py` 通过 |
| Reddit 真实预览 | NOT_EXECUTED | smoke flag 和凭据未设置 |
| Product Hunt 真实预览 | NOT_EXECUTED | smoke flag 和凭据未设置 |
| LLM 真实预览 | NOT_EXECUTED | smoke flag、base URL、model、key 未设置 |
| Embedding 真实预览 | NOT_EXECUTED | smoke flag、base URL、model、key 未设置 |
| 真实平台写库 | PASS_NOT_PERFORMED | `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=UNSET`，脚本显示 `write_enabled: False` |
| 公网暴露边界 | FAIL_BLOCKER | 发现既有 `cloudflared` tunnel 进程 |
| Compose 收尾 | PASS | `docker compose down` 后无运行服务 |

## 未跑通点清单

### P-001 真实平台预览未执行

状态：NOT_EXECUTED

原因：

- `SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=UNSET`
- `REDDIT_CLIENT_ID=UNSET`
- `REDDIT_CLIENT_SECRET=UNSET`
- `REDDIT_USER_AGENT=UNSET`
- `PRODUCT_HUNT_TOKEN=UNSET`

影响：

- 不能证明 Reddit/Product Hunt 真实接口可用。
- 不能进入生产 Go。

解决方案：

- 通过本机运行时环境注入 Reddit/Product Hunt 凭据。
- 显式设置 `SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true`。
- 保持 `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE` 不设置，继续预览不写库。

复测路径：

```bash
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_reddit_smoke.py
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_product_hunt_smoke.py
```

回滚方式：

- 取消环境变量。
- 停止 Compose 服务。
- 因本轮没有写库，无需数据库回滚。

### P-002 真实 LLM/Embedding 预览未执行

状态：NOT_EXECUTED

原因：

- `SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=UNSET`
- `SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=UNSET`
- `LLM_BASE_URL=UNSET`
- `LLM_MODEL=UNSET`
- `EMBEDDING_MODEL=UNSET`
- `LLM_API_KEY=UNSET`

影响：

- 不能证明真实 LLM/Embedding provider 可用。
- 不能进入生产 Go。

解决方案：

- 通过本机运行时环境注入 provider base URL、model 和 API key。
- 分别显式设置 `SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true` 和 `SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true`。
- 只记录状态、HTTP 类别和脱敏摘要，不记录 key。

复测路径：

```bash
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_llm_smoke.py
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_embedding_smoke.py
```

回滚方式：

- 取消环境变量。
- 停止 Compose 服务。

### P-003 发现既有公网 tunnel，与仅本机访问边界冲突

状态：FAIL_BLOCKER

观察：

```text
cloudflared tunnel --metrics 127.0.0.1:0 --url http://localhost:3000
```

影响：

- 本轮计划要求“不启用 tunnel、不做公网暴露、仅本机访问”。
- 即使本轮没有启动 tunnel，已有 tunnel 仍构成外部访问面。
- 生产 Go 条件中的“没有公网暴露”不满足。

解决方案：

- 需要 owner 明确批准后停止该 tunnel 进程。
- 停止后重新执行 `pgrep -fl 'cloudflared|trycloudflare' || true` 确认无残留。
- 如果后续确实需要公网访问，应另起“公网入口、HTTPS、鉴权、撤销方案”计划。

复测路径：

```bash
pgrep -fl 'cloudflared|trycloudflare' || true
python3 scripts/validate_no_secrets.py
```

回滚方式：

- 如果停止 tunnel 后需要恢复外部 demo，需要重新按批准流程启动新的 tunnel。

### P-004 工作树非 clean

状态：RESIDUAL_RISK

观察：

```text
 M apps/web/next-env.d.ts
?? AGENTS.md
?? apps/web/test-results/
?? current_state_report.md
?? docs/agents/
?? token_behavior_report.md
```

影响：

- 不影响本轮 local/mock 回归结论。
- 会影响发布、提交、审计和后续生产证明口径。

解决方案：

- 对每个路径做 keep/stage/ignore/remove 分类。
- 不要在未审批情况下删除或 revert。

复测路径：

```bash
git status --short --branch
```

回滚方式：

- 需要 owner 批准后按文件归属处理；本轮不执行清理。

## Go / No-Go 判断

结论：**NO-GO**。

Go 条件对照：

- local/mock 回归全 PASS：满足。
- Reddit、Product Hunt、LLM、Embedding 均 `PASS_REAL`：不满足，均为 `NOT_EXECUTED`。
- 没有真实写库：满足。
- 没有密钥泄露：满足。
- 没有公网暴露：不满足，发现既有 `cloudflared` tunnel。

## 追加执行记录：已批准停止 tunnel

时间：2026-05-01

Owner 已批准停止现有 `cloudflared` tunnel。执行结果：

| 命令 | 结果 | 退出码 | 关键输出 |
|---|---:|---:|---|
| `pgrep -fl 'cloudflared|trycloudflare' || true` | PASS_WITH_RISK | 0 | 停止前发现 `signalforge_tunnel` screen 和 `cloudflared tunnel --url http://localhost:3000` |
| `screen -S signalforge_tunnel -X quit` | PASS | 0 | screen 会话已退出 |
| `pkill -TERM -f 'cloudflared tunnel --metrics 127.0.0.1:0 --url http://localhost:3000'` | PASS | 0 | 终止残留 `cloudflared` 进程 |
| `pgrep -fl 'cloudflared|trycloudflare' || true` | PASS | 0 | 无输出，确认无 tunnel 残留 |

追加复核：

```text
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=UNSET
SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=UNSET
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=UNSET
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=UNSET
REDDIT_CLIENT_ID=UNSET
REDDIT_CLIENT_SECRET=UNSET
REDDIT_USER_AGENT=UNSET
PRODUCT_HUNT_TOKEN=UNSET
LLM_API_KEY=UNSET
OPENAI_API_KEY=UNSET
ANTHROPIC_API_KEY=UNSET
EMBEDDING_API_KEY=UNSET
LLM_BASE_URL=UNSET
LLM_MODEL=UNSET
EMBEDDING_MODEL=UNSET
```

结论：

- 公网 tunnel blocker 已解除。
- 当前 shell 仍未注入真实凭据和 smoke flags。
- 未重跑真实 preview，因为没有可用真实凭据，执行只会再次得到 `NOT_EXECUTED`。
- Compose 当前无运行服务。

## 后续测试路径

### 先解除访问面冲突

已完成。复核命令：

```bash
pgrep -fl 'cloudflared|trycloudflare' || true
```

### 再执行真实预览

在同一个 shell 或受控运行环境中注入必需 env，仅使用 SET/UNSET 方式报告：

```bash
docker compose -f infra/docker-compose.yml up -d
python3 scripts/wait_for_services.py
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_reddit_smoke.py
SIGNALFORGE_ALLOW_REAL_PLATFORM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_product_hunt_smoke.py
SIGNALFORGE_ALLOW_REAL_LLM_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_llm_smoke.py
SIGNALFORGE_ALLOW_REAL_EMBEDDING_SMOKE=true docker compose -f infra/docker-compose.yml run --rm api python /app/scripts/manual_embedding_smoke.py
docker compose -f infra/docker-compose.yml down
```

禁止项：

- 不设置 `SIGNALFORGE_ALLOW_REAL_PLATFORM_WRITE=true`。
- 不把密钥写入 `.env`、报告、日志、Git、API 响应或 raw payload。
- 不启动 tunnel。

## 残留风险

- 真实接口没有完成 `PASS_REAL`。
- 既有公网 tunnel 已按批准停止；后续不得在未批准情况下重新启动。
- Compose 运行时端口配置绑定 `0.0.0.0`，如果未来要求严格“仅本机”，需要另行评估端口绑定策略。
- Product Hunt 商业权限仍需在真实使用前明确。
- 当前分支和 release-freeze gate 的分支要求此前存在不一致，需要另行处理。

## 回滚方式

- 本轮新增报告文件可通过删除或 `git revert` 回滚。
- Compose 服务已停止：`docker compose -f infra/docker-compose.yml down`。
- 本轮没有真实写库，无需数据回滚。
- 本轮没有修改业务代码、schema、依赖、CI、部署、密钥或权限。
- tunnel 未由本轮启动；已在 owner 批准后停止。
