# SignalForge Round 1 Production Report

## 任务判断

结论：Round 1 production 状态为外部 demo 上线验证 PASS；这不是正式生产发布，也不代表系统已具备正式生产级认证、监控、备份、SLA 或容量保障。

## 当前目标

- 验证外部访问者可通过 Web tunnel 打开 SignalForge demo 页面。
- 验证外部同源 `/api/*` 可通过 Next proxy 访问 FastAPI。
- 验证报告中不泄露完整 `sf_token`。

## 已确认事实

- External Smoke Report 状态：PASS。
- 外部验证使用用户批准的临时 Cloudflare quick tunnel，验证完成后已停止。
- 外部 demo URL 已脱敏记录为：

```text
https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>
```

- External smoke 验证通过：
  - `/signals` HTML loaded and contained a required UI marker。
  - `/api/health` checked。
  - `/api/projects?page_size=1` checked。
  - `/api/settings/platforms` checked。
  - 未观察到 HTTP 500。
  - 未观察到 `Internal Error`。
  - 报告未记录完整 `sf_token`。

## 风险点

- 这是外部 demo 上线验证，不是正式生产。
- `sf_token` 是临时 demo 访问控制，不是长期认证机制。
- trycloudflare tunnel 或同类 tunnel 的可用性、稳定性、审计能力不等同于正式生产入口。
- 本轮未覆盖正式生产域名、TLS 证书管理、WAF、集中日志、告警、备份恢复、容量测试或故障演练。

## 推荐方案

Round 1 可对外进行 demo 验证；不得将本报告解读为正式生产上线批准。

## 改动边界

- 本报告仅记录 external demo production-like 验证结果。
- 未修改应用代码。
- 未执行 git 暂存、提交、重置或回滚。
- 未写入完整 `sf_token`。

## 执行命令

```bash
cloudflared tunnel --url http://localhost:3000
python3 scripts/validate_external_smoke.py --url 'https://subdivision-observer-females-karma.trycloudflare.com/signals?projectId=f7e9e589-64bb-4dbd-bace-6aec9b09d42f&sf_token=<redacted>' --check-api
```

## 验证结果

PASS。

## 残留问题

- 无 external demo Go-blocking 残留问题。
- 第一个 quick tunnel URL 出现 TLS EOF，已重新创建第二个 tunnel 并通过验证。
- 正式生产上线前仍需补齐生产级认证、域名、TLS、监控、日志、备份、容量与回滚演练。

## 回滚方式

- 关闭外部 tunnel。
- 停止本地 demo runtime：

```bash
docker compose -f infra/docker-compose.yml down
```

- 如需回滚本报告，恢复或删除 `production_report.md`。
