import { expect, test, type Page, type Route } from "@playwright/test";

const projectId = "project-1";
const signalA = "signal-1";
const signalB = "signal-2";

test.beforeEach(async ({ page }) => {
  await installApiMocks(page);
});

test("starts a new analysis without preserving the active project id", async ({ page }) => {
  await page.goto(`/onboarding?projectId=${projectId}`);
  await expect(page.getByRole("heading", { name: "创建个人信号项目" })).toBeVisible();
  await page.getByRole("link", { name: "新建分析" }).click();
  await expect(page).toHaveURL(/\/onboarding\?new=1$/);
});

test("runs the personal production UI workflow", async ({ page }) => {
  await page.goto("/onboarding");
  await expect(page.getByRole("heading", { name: "创建个人信号项目" })).toBeVisible();
  await expect(page.getByRole("combobox", { name: "项目选择器" })).toHaveValue(projectId);
  await page.getByLabel("项目名称").fill("个人生产 E2E");
  await page.getByLabel("包含关键词").fill("钱包引导, 价格清晰度");
  await page.getByLabel("排除关键词").fill("抽奖");
  await expect(page.getByLabel("包含关键词")).toHaveValue("钱包引导, 价格清晰度");
  await page.getByRole("button", { name: "创建项目并进入控制台" }).click();
  await expect(page).toHaveURL(/\/dashboard\?projectId=project-1/, { timeout: 15_000 });

  await page.goto(`/settings?projectId=${projectId}`);
  await page.getByRole("button", { name: "Test Connection" }).first().click();
  await expect(page.getByText("Mock connector is always available")).toBeVisible();
  await expect(page.getByText("encrypted_payload")).toHaveCount(0);

  await page.goto(`/logs?projectId=${projectId}`);
  await page.getByRole("button", { name: "运行采集" }).click();
  await expect(page.getByText("采集任务 成功")).toBeVisible();
  await expect(page.getByText("入库 5")).toBeVisible();

  await page.goto(`/dashboard?projectId=${projectId}`);
  await page.getByRole("button", { name: "运行处理" }).click();
  await expect(page.getByText("处理完成")).toBeVisible();

  await page.goto(`/signals?projectId=${projectId}`);
  await expect(page.getByRole("heading", { name: "需要更清晰的钱包提醒" }).first()).toBeVisible();
  await page.getByRole("button", { name: "保存" }).first().click();
  await page.getByRole("button", { name: "忽略" }).nth(1).click();
  await expect(page.getByText("https://example.test/source-1")).toBeVisible();
  await expect(page.getByText("验证提醒工作流。")).toBeVisible();

  await page.goto(`/opportunities?projectId=${projectId}`);
  await expect(page.getByText("Wallet onboarding alerts")).toBeVisible();

  await page.goto(`/reports?projectId=${projectId}`);
  await page.getByRole("button", { name: "Markdown 导出" }).click();
  await expect(page.getByRole("textbox", { name: "Markdown 预览" })).toContainText("source_url");
  await expect(page.getByRole("textbox", { name: "Markdown 预览" })).toContainText("recommended_action");
  await page.getByRole("button", { name: "CSV 导出" }).click();
  await expect(page.getByRole("heading", { name: "CSV 导出" })).toBeVisible();
  await expect(page.locator(".csvPreview")).toContainText("source_url");

  await expect(page.getByText("encrypted_payload")).toHaveCount(0);
  await expect(page.getByText("PRODUCT_HUNT_TOKEN")).toHaveCount(0);
  await expect(page.getByText("REDDIT_CLIENT_SECRET")).toHaveCount(0);
});

test("creates a production lifecycle run with explicit approval controls", async ({ page }) => {
  await page.goto(`/production?projectId=${projectId}`);
  await expect(page.getByRole("heading", { name: "Mac mini 本地生产生命周期" })).toBeVisible();
  await expect(page.getByText("创建运行")).toBeVisible();
  await expect(page.getByRole("button", { name: "创建并运行" })).toBeEnabled();

  await page.getByLabel("运行模式").selectOption("production");
  await expect(page.getByRole("button", { name: "创建并运行" })).toBeDisabled();
  await page.getByLabel("允许真实平台读取").check();
  await page.getByLabel("允许真实平台写入").check();
  await page.getByLabel("允许真实大模型调用").check();
  await page.getByLabel("显式确认").fill("确认");
  await expect(page.getByRole("button", { name: "创建并运行" })).toBeEnabled();

  await page.getByRole("button", { name: "创建并运行" }).click();
  await expect(page.getByText("运行完成")).toBeVisible();
  await expect(page.getByText("收口").first()).toBeVisible();
  await expect(page.getByText("job-1").first()).toBeVisible();
  await expect(page.getByText("门禁已就绪")).toBeVisible();
});

async function installApiMocks(page: Page) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const method = route.request().method();

    if (path === "/api/health") {
      return json(route, { status: "ok" });
    }

    if (path === "/api/projects" && method === "GET") {
      return json(route, {
        items: [project()],
        page: 1,
        page_size: 100,
        total: 1
      });
    }

    if (path === "/api/projects" && method === "POST") {
      return json(route, project(), 201);
    }

    if (path === `/api/projects/${projectId}/keywords`) {
      if (method === "POST") {
        return json(route, {
          id: `keyword-${Math.random()}`,
          project_id: projectId,
          keyword: "wallet onboarding",
          keyword_type: "main",
          language: "all",
          enabled: true,
          created_at: "2026-04-29T00:00:00.000Z",
          updated_at: "2026-04-29T00:00:00.000Z"
        }, 201);
      }
      return json(route, []);
    }

    if (path === "/api/settings/platforms") {
      return json(route, {
        platforms: [
          { platform: "reddit", phase: "P0", enabled_for_mvp: true, status: "missing_env" },
          { platform: "product_hunt", phase: "P0", enabled_for_mvp: true, status: "missing_env" },
          { platform: "x", phase: "P1", enabled_for_mvp: false, status: "coming_soon" },
          { platform: "discord", phase: "P2", enabled_for_mvp: false, status: "coming_soon" }
        ]
      });
    }

    if (path === "/api/settings/credentials/status") {
      return json(route, {
        credentials: [
          { platform: "reddit", status: "missing_env", credential_name: null, last_checked_at: null },
          { platform: "product_hunt", status: "missing_env", credential_name: null, last_checked_at: null },
          { platform: "x", status: "coming_soon", credential_name: null, last_checked_at: null },
          { platform: "discord", status: "coming_soon", credential_name: null, last_checked_at: null }
        ]
      });
    }

    if (path === "/api/settings/platforms/mock/test") {
      return json(route, {
        platform: "mock",
        status: "available",
        message: "Mock connector is always available for Personal Production v1.",
        checked_at: "2026-04-29T00:00:00.000Z",
        required_env_missing: []
      });
    }

    if (path === `/api/projects/${projectId}/collect` && method === "POST") {
      return json(route, {
        id: "job-1",
        project_id: projectId,
        status: "success",
        trigger_type: "manual",
        started_at: "2026-04-29T00:00:00.000Z",
        finished_at: "2026-04-29T00:01:00.000Z",
        error_summary: null,
        created_at: "2026-04-29T00:00:00.000Z",
        collector_execution: "mock",
        log: collectionLog()
      });
    }

    if (path === `/api/projects/${projectId}/collection-logs`) {
      return json(route, { items: [collectionLog()], page: 1, page_size: 50, total: 1 });
    }

    if (path === `/api/projects/${projectId}/process` && method === "POST") {
      return json(route, processingResponse());
    }

    if (path === `/api/projects/${projectId}/signals`) {
      return json(route, { items: [signal(signalA), signal(signalB)], page: 1, page_size: 100, total: 2 });
    }

    if (path === `/api/signals/${signalA}/status` || path === `/api/signals/${signalB}/status`) {
      return json(route, signal(path.includes(signalA) ? signalA : signalB));
    }

    if (path === `/api/projects/${projectId}/processing-summary`) {
      return json(route, processingResponse());
    }

    if (path === "/api/production/runs") {
      if (method === "POST") {
        return json(route, productionRun(), 201);
      }

      return json(route, { items: [productionRun()], page: 1, page_size: 20, total: 1 });
    }

    if (path === `/api/projects/${projectId}/opportunities`) {
      return json(route, { items: [opportunity()], page: 1, page_size: 100, total: 1 });
    }

    if (path === `/api/projects/${projectId}/reports/markdown` && method === "POST") {
      return json(route, {
        format: "markdown",
        content: "# Report\n\nsource_url: https://example.test/source-1\nrecommended_action: 验证提醒工作流。",
        generated_at: "2026-04-29T00:00:00.000Z"
      });
    }

    if (path === `/api/projects/${projectId}/reports/csv` && method === "POST") {
      return json(route, {
        format: "csv",
        filename: "signalforge-e2e.csv",
        content_type: "text/csv",
        content: "signal_id,source_url,recommended_action\nsignal-1,https://example.test/source-1,验证提醒工作流。",
        generated_at: "2026-04-29T00:00:00.000Z"
      });
    }

    return json(route, { error: { code: "not_mocked", message: path, details: {} } }, 404);
  });
}

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    body: JSON.stringify(body),
    contentType: "application/json",
    status
  });
}

function project() {
  return {
    id: projectId,
    name: "Personal Production E2E",
    description: "E2E project",
    platforms_enabled: { mock: true },
    collection_frequency: "manual",
    created_at: "2026-04-29T00:00:00.000Z",
    updated_at: "2026-04-29T00:00:00.000Z"
  };
}

function collectionLog() {
  return {
    id: "log-1",
    job_id: "job-1",
    platform: "mock",
    status: "success",
    items_collected: 5,
    items_inserted: 5,
    items_skipped: 0,
    error_message: null,
    rate_limit_remaining: null,
    rate_limit_reset_at: null,
    created_at: "2026-04-29T00:00:00.000Z"
  };
}

function productionRun() {
  return {
    id: "production-run-1",
    project_id: projectId,
    status: "success",
    stage: "closeout",
    collection_mode: "mock",
    processing_mode: "fallback_only",
    allow_real_platform_write: true,
    allow_real_llm: true,
    allow_real_embedding: false,
    env_preflight: { safe_execution: true },
    result_summary: {
      collection: { job_id: "job-1", status: "success", items_inserted: 5 },
      processing: processingResponse()
    },
    error_summary: null,
    rollback_hint: null,
    redacted_logs: [],
    started_at: "2026-04-29T00:00:00.000Z",
    finished_at: "2026-04-29T00:01:00.000Z",
    created_at: "2026-04-29T00:00:00.000Z",
    updated_at: "2026-04-29T00:01:00.000Z"
  };
}

function signal(id: string) {
  return {
    id,
    raw_item_id: `raw-${id}`,
    project_id: projectId,
    is_need_signal: true,
    signal_type: "feature_request",
    pain_level: 82,
    clarity_score: 80,
    urgency_score: 75,
    business_relevance: 70,
    model_confidence: 88,
    signal_confidence: 86,
    summary_zh: id === signalA ? "需要更清晰的钱包提醒" : "需要更好的报告导出",
    recommended_action: "验证提醒工作流。",
    user_feedback: null,
    status: "new",
    created_at: "2026-04-29T00:00:00.000Z",
    updated_at: "2026-04-29T00:00:00.000Z",
    platform: "mock",
    source_url: id === signalA ? "https://example.test/source-1" : "https://example.test/source-2",
    content_excerpt: "Need alerts for wallet onboarding.",
    keyword_hits: ["wallet", "onboarding"],
    engagement: null,
    created_at_source: null
  };
}

function opportunity() {
  return {
    id: "opportunity-1",
    project_id: projectId,
    cluster_id: "cluster-1",
    title: "Wallet onboarding alerts",
    description: "Users want clearer wallet onboarding alerts.",
    status: "new",
    opportunity_score: 84,
    evidence_count: 3,
    platform_distribution: { mock: 3 },
    last_seen_at: "2026-04-29T00:00:00.000Z",
    created_at: "2026-04-29T00:00:00.000Z",
    updated_at: "2026-04-29T00:00:00.000Z"
  };
}

function processingResponse() {
  return {
    project_id: projectId,
    mode: "mock",
    reprocess: false,
    processed_in_run: 5,
    skipped_existing: 0,
    skipped_deleted: 0,
    status: "success",
    details: {},
    total_raw_items: 5,
    processed_raw_items: 5,
    total_signals: 3,
    high_value_signals: 1,
    high_value_ratio: 0.33,
    noise_ratio: 0,
    llm_json_failure_count: 0,
    fallback_classification_count: 0,
    cluster_coverage_rate: 1,
    opportunity_count: 1,
    embedding_count: 3,
    cluster_count: 1,
    top_5_high_value_signals: []
  };
}
