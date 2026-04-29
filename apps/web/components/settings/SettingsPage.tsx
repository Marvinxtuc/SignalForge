"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "../../lib/api";
import { formatDateTime, formatStatusLabel, platformLabel } from "../../lib/format";
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
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">设置</p>
          <h1 className="pageTitle">平台设置</h1>
          <p className="pageSubtitle">
            只读平台与凭据状态。不会展示密钥载荷。
          </p>
        </div>
      </header>

      {state.status === "loading" ? <LoadingState label="正在加载设置" /> : null}
      {state.status === "error" ? (
        <ErrorState error={state.error} title="无法加载设置" />
      ) : null}

      {state.status === "ready" ? (
        <div className="integrationList">
          {rows.map((row) => (
            <article className="integrationRow" key={row.platform}>
              <div className="integrationIdentity">
                <span className="integrationIcon" aria-hidden="true">
                  {platformInitial(row.platform)}
                </span>
                <div>
                  <p className="integrationName">{platformLabel(row.platform)}</p>
                  <p className="integrationMeta">
                    最近检查 {formatDateTime(row.lastCheckedAt)}。本地 MVP 的只读状态。
                  </p>
                </div>
              </div>
              <div className="integrationBadges">
                <Badge tone={phaseTone(row.phase)}>{row.phase}</Badge>
                <Badge tone={row.enabledForMvp ? "success" : "neutral"}>
                  {row.enabledForMvp ? "MVP 已启用" : "MVP 未启用"}
                </Badge>
                <Badge tone={credentialTone(row.platformStatus)}>
                  {formatStatusLabel(row.platformStatus)}
                </Badge>
                <Badge tone={credentialTone(row.credentialStatus)}>
                  凭据 {formatStatusLabel(row.credentialStatus)}
                </Badge>
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function platformInitial(platform: PlatformName): string {
  if (platform === "product_hunt") {
    return "PH";
  }

  return platform.slice(0, 1).toUpperCase();
}

function fallbackPhase(platform: PlatformName): PlatformPhase {
  if (platform === "reddit" || platform === "product_hunt") {
    return "P0";
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
