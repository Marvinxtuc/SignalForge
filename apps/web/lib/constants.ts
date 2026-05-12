export const DEFAULT_SERVER_API_BASE_URL = "http://api:8000";
export const SERVER_API_BASE_URL =
  process.env.SERVER_API_BASE_URL?.replace(/\/+$/, "") || DEFAULT_SERVER_API_BASE_URL;

export const DEFAULT_PUBLIC_API_BASE_URL = "/api";
export const HAS_PUBLIC_API_BASE_URL_OVERRIDE = Boolean(
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim()
);
export const PUBLIC_API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || DEFAULT_PUBLIC_API_BASE_URL;

export const API_REQUEST_TIMEOUT_MS = 10_000;

export const DEFAULT_PROJECT_NAME = "Polymarket Opportunity Radar";

export const ROUTES = {
  onboarding: "/onboarding",
  signals: "/signals",
  dashboard: "/dashboard",
  opportunities: "/opportunities",
  production: "/production",
  logs: "/logs",
  reports: "/reports",
  settings: "/settings"
} as const;

export const NAV_ITEMS = [
  { href: ROUTES.onboarding, label: "引导", hint: "开始" },
  { href: ROUTES.signals, label: "信号收件箱", hint: "核心" },
  { href: ROUTES.dashboard, label: "仪表盘", hint: "摘要" },
  { href: ROUTES.opportunities, label: "机会看板", hint: "处理" },
  { href: ROUTES.production, label: "生产运行", hint: "审批" },
  { href: ROUTES.logs, label: "运行日志", hint: "采集" },
  { href: ROUTES.reports, label: "报告导出", hint: "导出" },
  { href: ROUTES.settings, label: "设置", hint: "管理" }
] as const;
