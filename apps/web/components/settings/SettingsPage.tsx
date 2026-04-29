"use client";

import { useEffect, useMemo, useState } from "react";
import type { CSSProperties, ReactNode } from "react";
import { api } from "../../lib/api";
import { formatDateTime, platformLabel } from "../../lib/format";
import type {
  CredentialStatus,
  CredentialStatusItem,
  PlatformName,
  PlatformPhase,
  PlatformStatus
} from "../../lib/types";
import { Badge } from "../ui/Badge";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

type SettingsState =
  | { status: "loading" }
  | { status: "ready"; platforms: PlatformStatus[]; credentials: CredentialStatusItem[] }
  | { status: "error"; error: unknown };

const REQUIRED_PLATFORMS: PlatformName[] = ["reddit", "product_hunt", "x", "discord"];

export function SettingsPage() {
  const [state, setState] = useState<SettingsState>({ status: "loading" });

  useEffect(() => {
    let active = true;

    Promise.all([api.settings.platforms(), api.settings.credentialStatus()])
      .then(([platformsResponse, credentialResponse]) => {
        if (active) {
          setState({
            status: "ready",
            platforms: platformsResponse.platforms,
            credentials: credentialResponse.credentials
          });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({ status: "error", error });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const rows = useMemo(() => {
    if (state.status !== "ready") {
      return [];
    }

    return REQUIRED_PLATFORMS.map((platform) => {
      const platformStatus = state.platforms.find((item) => item.platform === platform);
      const credentialStatus = state.credentials.find((item) => item.platform === platform);

      return {
        platform,
        phase: platformStatus?.phase ?? fallbackPhase(platform),
        enabledForMvp: platformStatus?.enabled_for_mvp ?? false,
        platformStatus: platformStatus?.status ?? "missing",
        credentialStatus: credentialStatus?.status ?? "missing",
        lastCheckedAt: credentialStatus?.last_checked_at ?? null
      };
    });
  }, [state]);

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <header style={{ display: "grid", gap: 4 }}>
        <p className="sectionLabel">Settings</p>
        <h1 style={{ fontSize: 24, lineHeight: 1.2, margin: 0 }}>Platform settings</h1>
        <p className="stateText" style={{ maxWidth: 760 }}>
          Read-only platform and credential status. Secret payloads are not displayed.
        </p>
      </header>

      {state.status === "loading" ? <LoadingState label="Loading settings" /> : null}
      {state.status === "error" ? (
        <ErrorState error={state.error} title="Unable to load settings" />
      ) : null}

      {state.status === "ready" ? (
        <div style={{ overflowX: "auto" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <Th>Platform</Th>
                <Th>Phase</Th>
                <Th>MVP</Th>
                <Th>Platform status</Th>
                <Th>Credential status</Th>
                <Th>Last checked</Th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.platform}>
                  <Td>{platformLabel(row.platform)}</Td>
                  <Td>
                    <Badge tone={phaseTone(row.phase)}>{row.phase}</Badge>
                  </Td>
                  <Td>{row.enabledForMvp ? "Enabled" : "Disabled"}</Td>
                  <Td>
                    <Badge tone={credentialTone(row.platformStatus)}>{row.platformStatus}</Badge>
                  </Td>
                  <Td>
                    <Badge tone={credentialTone(row.credentialStatus)}>
                      {row.credentialStatus}
                    </Badge>
                  </Td>
                  <Td>{formatDateTime(row.lastCheckedAt)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function fallbackPhase(platform: PlatformName): PlatformPhase {
  if (platform === "reddit") {
    return "P0";
  }

  if (platform === "product_hunt") {
    return "P1";
  }

  return "P2";
}

function phaseTone(phase: PlatformPhase): "neutral" | "success" | "warning" | "danger" {
  if (phase === "P0") {
    return "success";
  }

  if (phase === "P1") {
    return "warning";
  }

  return "neutral";
}

function credentialTone(status: CredentialStatus): "neutral" | "success" | "warning" | "danger" {
  if (status === "configured") {
    return "success";
  }

  if (status === "invalid" || status === "permission_limited") {
    return "danger";
  }

  if (status === "disabled") {
    return "warning";
  }

  return "neutral";
}

function Th({ children }: { children: ReactNode }) {
  return <th style={headerCellStyle}>{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td style={bodyCellStyle}>{children}</td>;
}

const tableStyle: CSSProperties = {
  width: "100%",
  minWidth: 760,
  borderCollapse: "collapse",
  border: "1px solid var(--border)",
  background: "var(--surface)"
};

const headerCellStyle: CSSProperties = {
  padding: "10px 12px",
  borderBottom: "1px solid var(--border)",
  color: "var(--muted)",
  fontSize: 12,
  fontWeight: 750,
  textAlign: "left",
  whiteSpace: "nowrap"
};

const bodyCellStyle: CSSProperties = {
  padding: "10px 12px",
  borderBottom: "1px solid var(--border)",
  color: "var(--text)",
  verticalAlign: "top"
};
