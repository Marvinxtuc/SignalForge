export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "从未";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "无效日期";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  return new Intl.NumberFormat("zh-CN").format(value);
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  return `${Math.round(value * 100)}%`;
}

export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }

  return `${Math.round(value)}/100`;
}

export function platformLabel(value: string | null | undefined): string {
  if (!value) {
    return "未知";
  }

  const labels: Record<string, string> = {
    reddit: "Reddit",
    product_hunt: "Product Hunt",
    x: "X",
    discord: "Discord",
    mock: "模拟平台",
    demo: "演示"
  };

  return labels[value] ?? labelFromSnakeCase(value);
}

export function truncateText(value: string | null | undefined, maxLength = 120): string {
  if (!value) {
    return "";
  }

  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, Math.max(0, maxLength - 1))}...`;
}

export function formatStatusLabel(value: string | null | undefined): string {
  if (!value) {
    return "未知";
  }

  const labels: Record<string, string> = {
    new: "新建",
    saved: "已保存",
    ignored: "已忽略",
    reviewed: "已复核",
    success: "成功",
    completed: "已完成",
    ok: "正常",
    failed: "失败",
    error: "错误",
    partial: "部分完成",
    partial_failed: "部分失败",
    rate_limited: "速率受限",
    warning: "警告",
    disabled: "已禁用",
    missing: "未配置",
    configured: "已配置",
    invalid: "无效",
    permission_limited: "权限受限",
    running: "运行中",
    pending: "等待中",
    fallback_only: "仅兜底",
    mock: "模拟",
    preview: "预览",
    production: "生产",
    preflight: "预检",
    collect: "采集",
    process: "处理",
    review: "复核",
    report: "报告",
    closeout: "收口",
    closed: "已关闭",
    no_go_real_provider: "真实服务未放行",
    preflight_only: "仅预检",
    preflight_passed: "预检通过"
  };

  return labels[value] ?? labelFromSnakeCase(value);
}

export function formatSignalTypeLabel(value: string | null | undefined): string {
  if (!value) {
    return "未知类型";
  }

  const labels: Record<string, string> = {
    complaint: "投诉",
    feature_request: "功能需求",
    alternative_search: "替代方案搜索",
    pricing_issue: "价格问题",
    security_concern: "安全担忧",
    workflow_pain: "流程痛点",
    integration_need: "集成需求",
    learning_barrier: "学习障碍",
    positive_feedback: "正向反馈",
    noise: "噪声"
  };

  return labels[value] ?? labelFromSnakeCase(value);
}

export function formatFeedbackLabel(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }

  const labels: Record<string, string> = {
    valuable: "有价值",
    not_valuable: "无价值",
    wrong_type: "类型错误",
    ignored: "忽略反馈"
  };

  return labels[value] ?? labelFromSnakeCase(value);
}

function labelFromSnakeCase(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
