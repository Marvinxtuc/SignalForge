# SignalForge Round 1 Security Review

## 结论

PASS

未发现 P0 泄露或 NO-GO 阻断项。本轮仅写入 `security_review.md`，未写入 `blocking_issue.md`。

## 检查范围

- Token/query/no-secrets/smoke 脱敏检查。
- `sf_token` 是否被 Next.js proxy 转发到 FastAPI。
- `authorization`、`cookie`、`sf_token` 相关 header 是否被前端 proxy 转发。
- `scripts/validate_external_smoke.py` 是否脱敏输出 URL。
- 前端 Settings/credential 展示是否暴露 `encrypted_payload` 或 credential 值。
- 是否存在正式认证系统伪装，例如登录、session、JWT、多用户认证声明。

重点文件：

- `apps/web/app/api/[...path]/route.ts`
- `apps/web/lib/api.ts`
- `apps/web/lib/query.ts`
- `apps/web/components/settings/SettingsPage.tsx`
- `apps/api/app/main.py`
- `apps/api/app/config.py`
- `apps/api/app/services/settings.py`
- `apps/api/app/schemas/settings.py`
- `scripts/validate_external_smoke.py`
- `scripts/validate_no_secrets.py`
- `external_smoke_report.md`
- `frontend_change_report.md`
- `infra/docker-compose.yml`

## 发现项

### 已确认事实

- PASS: `sf_token` 不转发 FastAPI。`apps/web/app/api/[...path]/route.ts` 在 upstream URL 构造时跳过 `sf_token` query；同文件 header denylist 包含 `authorization`、`cookie`、`sf-token`、`sf_token`、`x-sf-token`。
- PASS: FastAPI 不通过该 proxy 下发 cookie。proxy response header denylist 包含 `set-cookie`。
- PASS: 前端 query helper allowlist 仅包含 `projectId` 与 `sf_token`，未发现任意 query 扩散。
- PASS: `scripts/validate_external_smoke.py` 的 `sanitize_url()` 会把 `sf_token` 输出为 `<redacted>`；通过/失败路径均使用脱敏 URL。
- PASS: `python3 scripts/validate_no_secrets.py` 通过，未发现常见真实 secret、bearer token、private key 或长 secret-like assignment。
- PASS: Settings credential API schema 只返回 `platform`、`status`、`credential_name`、`last_checked_at`，不包含 `encrypted_payload`；前端 Settings 页面不渲染 `encrypted_payload`。
- PASS: 未发现新增正式认证系统实现或伪装。README/acceptance 文档明确 `Auth / multi-user` 不在本轮范围；代码中未发现 login/session/JWT/CSRF 认证实现。

### 判断

- `sf_token` 是临时 demo query 访问控制信号，不是正式认证系统。它被前端页面 URL 保留以维持 demo 访问，但被 proxy 从 FastAPI upstream query 中剔除。
- `infra/docker-compose.yml` 中的 `signalforge_dev_password` 是本地开发数据库密码，当前 no-secrets validator 未判定为真实泄露；仍不应复用于生产。

### 未发现

- 未发现应用代码主动将 `authorization`、`cookie`、`sf_token`、`sf-token`、`x-sf-token` 转发到 FastAPI。
- 未发现 `sf_token` 完整值写入现有报告。
- 未发现前端 `console.*` 或后端 logging 输出 token/credential 的路径。
- 未发现 P0 credential 暴露或必须阻塞事项。

## 执行命令

```bash
pwd && rg --files -g '!*node_modules*' -g '!*.png' -g '!*.jpg' -g '!*.jpeg' -g '!*.gif' -g '!*.ico'
git status --short
rg -n "sf_token|validate_external_smoke|smoke|token|credential|secret|password|authorization|api[_-]?key|FastAPI|fastapi|logger|logging|print\(" -S . -g '!*node_modules*' -g '!*.png' -g '!*.jpg' -g '!*.jpeg' -g '!*.gif'
sed -n '1,260p' 'apps/web/app/api/[...path]/route.ts'
sed -n '1,260p' apps/web/lib/query.ts
sed -n '1,220p' scripts/validate_external_smoke.py
sed -n '1,180p' scripts/validate_no_secrets.py
python3 scripts/validate_no_secrets.py
rg -n "console\.|logger|logging|print\(|sf_token|sf-token|x-sf-token|authorization|cookie|set-cookie|credential|encrypted_payload|raw_payload|secret|token|auth|login|session" apps/web apps/api scripts infra README.md docs sop -S -g '!*node_modules*' -g '!.next*'
rg -n "NEXT_PUBLIC|SERVER_API_BASE_URL|API_BASE|AUTH|TOKEN|SECRET|PASSWORD|COOKIE|sf_token|credential" apps/web apps/api/app/config.py infra/docker-compose.yml .env.example -S
sed -n '1,230p' apps/web/lib/api.ts
sed -n '230,380p' apps/web/lib/api.ts
sed -n '1,220p' apps/web/components/settings/SettingsPage.tsx
sed -n '1,180p' apps/api/app/main.py
sed -n '1,140p' apps/api/app/config.py
sed -n '1,220p' apps/api/tests/test_cors_config.py
sed -n '1,220p' apps/api/tests/test_settings_api.py
sed -n '1,260p' apps/api/app/schemas/settings.py
sed -n '1,120p' apps/api/app/services/settings.py
rg -n "console\.|logger\.|logging\.|print\(.*(token|secret|credential|authorization|cookie|sf_token)|raise .*token|message.*token|details.*token" apps/web apps/api scripts -S -g '!*node_modules*'
python3 -m pytest apps/api/tests/test_cors_config.py apps/api/tests/test_settings_api.py apps/api/tests/test_p0_connector_no_token_leak.py
python3 scripts/validate_frontend_mvp.py
rg -n "sf_token\s*=\s*['\"][^'\"]{8,}|sf_token=[A-Za-z0-9._~+/=-]{8,}|Bearer\s+[A-Za-z0-9._-]{20,}|authorization\s*[:=]\s*['\"]Bearer|APP_SECRET_KEY\s*=\s*[^\s#]+|PRODUCT_HUNT_TOKEN\s*=\s*[^\s#]+|REDDIT_CLIENT_SECRET\s*=\s*[^\s#]+" . -S -g '!*node_modules*' -g '!.git*' -g '!*.png' -g '!*.jpg' -g '!*.jpeg' -g '!*.gif'
rg -n "login|logout|sign in|signin|session|auth|authentication|authenticated|user|password|jwt|csrf" apps/web apps/api README.md docs/acceptance docs/runbooks sop -S -g '!*node_modules*'
python3 - <<'PY'
from scripts.validate_external_smoke import sanitize_url
url = 'https://example.test/signals?projectId=p1&sf_token=super-secret-demo-token&other=value'
print(sanitize_url(url))
PY
sed -n '1,120p' external_smoke_report.md
sed -n '1,180p' frontend_change_report.md
git diff -- 'apps/web/app/api/[...path]/route.ts' apps/web/lib/query.ts scripts/validate_external_smoke.py scripts/validate_no_secrets.py apps/api/app/main.py apps/api/app/config.py infra/docker-compose.yml
npx tsc --noEmit --incremental false
```

## 验证结果

- `python3 scripts/validate_no_secrets.py`: PASS, 输出 `PASS: no secrets validation`。
- `python3 scripts/validate_frontend_mvp.py`: PASS, 包含 `query token helper only preserves approved query values`、`settings page does not render encrypted_payload`、`no forbidden execution options or token-like values found in frontend source`。
- `npx tsc --noEmit --incremental false` in `apps/web`: PASS，无输出。
- `sanitize_url()` 实测输出：`https://example.test/signals?projectId=p1&sf_token=<redacted>&other=value`。
- `external_smoke_report.md`: PASS，报告中的 external URL 与命令均使用 `sf_token=<redacted>`。
- `frontend_change_report.md`: 记录临时 Next dev server smoke 中 `GET /api/health?sf_token=should-not-forward` 返回 HTTP 200。
- `python3 -m pytest ...`: 未执行成功，原因是当前全局 Python 3.14 环境无 `pytest` 模块。未安装依赖，未改变环境。

## 残留风险

- `sf_token` 仍在浏览器 URL 中传播，可能进入浏览器历史、Referer、截图或外部边缘日志；仅适合临时 demo，不可视为长期认证。
- `validate_external_smoke.py` 当前只脱敏 `sf_token`，如果后续引入其他 query token，需要同步扩展脱敏规则。
- 本轮以只读审查和现有 validator 为主，未启动新的外部 tunnel 复测；external smoke 结果来自 `external_smoke_report.md` 和脚本脱敏实测。
- 后端 pytest 因本机全局环境缺少 `pytest` 未能复跑；静态测试文件存在对应断言，但本轮未取得 pytest 运行通过证据。

## 修改文件清单

- `security_review.md`

## 改动目的

- 输出 Round 1 Security Agent 审查报告，给外部总控与审计系统复核。

## 回滚方式

- 回滚本轮唯一写入：删除或还原 `security_review.md`。
- 未修改应用代码、配置、数据库或依赖；无需服务回滚。
