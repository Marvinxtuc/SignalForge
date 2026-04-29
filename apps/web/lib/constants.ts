export const DEFAULT_API_BASE_URL = "http://localhost:8000";
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || DEFAULT_API_BASE_URL;

export const API_REQUEST_TIMEOUT_MS = 10_000;

export const DEFAULT_PROJECT_NAME = "Polymarket Opportunity Radar";

export const ROUTES = {
  signals: "/signals",
  dashboard: "/dashboard",
  opportunities: "/opportunities",
  logs: "/logs",
  reports: "/reports",
  settings: "/settings"
} as const;

export const NAV_ITEMS = [
  { href: ROUTES.signals, label: "Signal Inbox", hint: "Core" },
  { href: ROUTES.dashboard, label: "Dashboard", hint: "Summary" },
  { href: ROUTES.opportunities, label: "Opportunities", hint: "Pipeline" },
  { href: ROUTES.logs, label: "Logs", hint: "Collection" },
  { href: ROUTES.reports, label: "Reports", hint: "Exports" },
  { href: ROUTES.settings, label: "Settings", hint: "Admin" }
] as const;
