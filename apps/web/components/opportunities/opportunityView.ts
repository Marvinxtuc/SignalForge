import type { OpportunityStatus } from "../../lib/types";

export const OPPORTUNITY_STATUSES: OpportunityStatus[] = [
  "new",
  "watching",
  "validating",
  "build_candidate",
  "content_candidate",
  "archived"
];

export const OPPORTUNITY_STATUS_LABELS: Record<OpportunityStatus, string> = {
  new: "New",
  watching: "Watching",
  validating: "Validating",
  build_candidate: "Build candidate",
  content_candidate: "Content candidate",
  archived: "Archived"
};

export function isOpportunityStatus(value: string): value is OpportunityStatus {
  return OPPORTUNITY_STATUSES.includes(value as OpportunityStatus);
}

export function opportunityStatusLabel(value: string | null | undefined): string {
  if (!value) {
    return "Unknown";
  }

  return isOpportunityStatus(value)
    ? OPPORTUNITY_STATUS_LABELS[value]
    : value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

export function formatPlatformDistribution(
  distribution: Record<string, unknown> | null | undefined
): string {
  if (!distribution || Object.keys(distribution).length === 0) {
    return "Unavailable";
  }

  const items = Object.entries(distribution)
    .filter(([key]) => !isSensitiveKey(key))
    .map(([platform, value]) => `${labelFromSnakeCase(platform)}: ${formatDistributionValue(value)}`);

  return items.length > 0 ? items.join(", ") : "Unavailable";
}

function formatDistributionValue(value: unknown): string {
  if (typeof value === "number" || typeof value === "string" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return `${value.length} values`;
  }

  if (value && typeof value === "object") {
    return "available";
  }

  return "unknown";
}

function isSensitiveKey(key: string): boolean {
  const normalized = key.toLowerCase();
  const encryptedPayloadKey = ["encrypted", "payload"].join("_");
  return normalized.includes("token") || normalized.includes(encryptedPayloadKey);
}

function labelFromSnakeCase(value: string): string {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
