import type { NextRequest } from "next/server";

export const OWNER_SESSION_COOKIE = "signalforge_owner_session";

const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);

export function isOwnerAuthRequired(): boolean {
  return TRUE_VALUES.has((process.env.SIGNALFORGE_REQUIRE_OWNER_AUTH ?? "").trim().toLowerCase());
}

export function getOwnerSessionToken(): string | null {
  const token = process.env.SIGNALFORGE_OWNER_SESSION_TOKEN?.trim();
  return token ? token : null;
}

export function getOwnerApiToken(): string | null {
  const token = process.env.SIGNALFORGE_OWNER_API_TOKEN?.trim();
  return token ? token : null;
}

export function verifyOwnerPassword(password: string): boolean {
  const expected = process.env.SIGNALFORGE_OWNER_PASSWORD?.trim();
  return Boolean(expected) && constantTimeEqual(password, expected ?? "");
}

export function isValidOwnerSessionValue(value: string | undefined | null): boolean {
  const expected = getOwnerSessionToken();
  return Boolean(expected && value && constantTimeEqual(value, expected));
}

export function hasValidOwnerSession(request: NextRequest): boolean {
  return isValidOwnerSessionValue(request.cookies.get(OWNER_SESSION_COOKIE)?.value);
}

export function ownerAuthConfigError(): string | null {
  if (!isOwnerAuthRequired()) {
    return null;
  }

  if (!process.env.SIGNALFORGE_OWNER_PASSWORD?.trim()) {
    return "SIGNALFORGE_OWNER_PASSWORD is required when owner auth is enabled.";
  }

  if (!getOwnerSessionToken()) {
    return "SIGNALFORGE_OWNER_SESSION_TOKEN is required when owner auth is enabled.";
  }

  if (!getOwnerApiToken()) {
    return "SIGNALFORGE_OWNER_API_TOKEN is required when owner auth is enabled.";
  }

  return null;
}

function constantTimeEqual(left: string, right: string): boolean {
  const maxLength = Math.max(left.length, right.length);
  let diff = left.length ^ right.length;

  for (let index = 0; index < maxLength; index += 1) {
    diff |= (left.charCodeAt(index) || 0) ^ (right.charCodeAt(index) || 0);
  }

  return diff === 0;
}
