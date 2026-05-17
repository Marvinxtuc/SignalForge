"use client";

import { useEffect, useMemo, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import { formatDateTime, formatStatusLabel, platformLabel } from "../../lib/format";
import type {
  CredentialStatus,
  CredentialStatusItem,
  PlatformEnvTestResponse,
  PlatformName,
  PlatformPhase,
  PlatformStatus
} from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

type SettingsState =
  | { status: "loading" }
  | { status: "ready"; platforms: PlatformStatus[]; credentials: CredentialStatusItem[] }
  | { status: "error"; error: unknown };

type SettingsPlatform = "mock" | PlatformName;

const REQUIRED_PLATFORMS: SettingsPlatform[] = ["mock", "reddit", "product_hunt", "x", "discord"];

const REQUIRED_ENV_COUNTS: Partial<Record<SettingsPlatform, number>> = {
  reddit: 3,
  product_hunt: 1
};

export function SettingsPage() {
  const [state, setState] = useState<SettingsState>({ status: "loading" });
  const [testResults, setTestResults] = useState<Record<string, PlatformEnvTestResponse>>({});
  const [testingPlatform, setTestingPlatform] = useState<string | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

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
      const platformStatus =
        platform === "mock" ? null : state.platforms.find((item) => item.platform === platform);
      const credentialStatus =
        platform === "mock" ? null : state.credentials.find((item) => item.platform === platform);
      const testResult = testResults[platform];

      return {
        platform,
        requiredEnvCount: REQUIRED_ENV_COUNTS[platform] ?? 0,
        phase: platformStatus?.phase ?? fallbackPhase(platform),
        enabledForMvp: platform === "mock" ? true : platformStatus?.enabled_for_mvp ?? false,
        platformStatus: testResult?.status ?? platformStatus?.status ?? fallbackStatus(platform),
        credentialStatus: testResult?.status ?? credentialStatus?.status ?? fallbackStatus(platform),
        lastCheckedAt: testResult?.checked_at ?? credentialStatus?.last_checked_at ?? null
      };
    });
  }, [state, testResults]);

  async function testPlatform(platform: SettingsPlatform) {
    setTestingPlatform(platform);
    setTestError(null);

    try {
      const response = await api.settings.testPlatform(platform);
      setTestResults((current) => ({ ...current, [platform]: response }));
    } catch (error) {
      setTestError(formatActionError(error));
    } finally {
      setTestingPlatform(null);
    }
  }

  return (
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">设置</p>
          <h1 className="pageTitle">平台设置</h1>
          <p className="pageSubtitle">
            个人 env 配置工作台。只显示配置状态，不保存、不展示、不返回敏感值。
          </p>
        </div>
      </header>

      {testError ? (
        <p className="inlineError" role="alert">
          {testError}
        </p>
      ) : null}

      {state.status === "loading" ? <LoadingState label="正在加载设置" /> : null}
      {state.status === "error" ? <ErrorState error={state.error} title="无法加载设置" /> : null}

      {state.status === "ready" ? (
        <>
          <section className="surfacePanel" aria-labelledby="env-status-title">
            <div className="pageHeader">
              <div>
                <h2 className="opportunityCardTitle" id="env-status-title">
                  Env Status Workspace
                </h2>
                <p className="selectorMeta">
                  通过本地 .env 配置个人平台访问；页面只展示状态，不显示变量名或敏感值。
                </p>
              </div>
              <Badge tone="neutral">No credential CRUD</Badge>
            </div>
          </section>

          <div className="integrationList">
            {rows.map((row) => (
              <article className="integrationRow" key={row.platform}>
                <div className="integrationIdentity">
                  <span className="integrationIcon" aria-hidden="true">
                    {platformInitial(row.platform)}
                  </span>
                  <div>
                    <p className="integrationName">{platformLabelSafe(row.platform)}</p>
                    <p className="integrationMeta">{envHelpText(row.platform)}</p>
                    <p className="integrationMeta">最近检查 {formatDateTime(row.lastCheckedAt)}。</p>
                    {testResults[row.platform] ? (
                      <p className="integrationMeta">
                        {sanitizeSecretMarkers(testResults[row.platform].message)}
                        {testResults[row.platform].required_env_missing.length > 0
                          ? ` 缺少 ${testResults[row.platform].required_env_missing.length} 个本地环境变量。`
                          : ""}
                      </p>
                    ) : null}
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
                  <Button
                    disabled={testingPlatform !== null}
                    onClick={() => void testPlatform(row.platform)}
                    size="small"
                    type="button"
                  >
                    {testingPlatform === row.platform ? "检测中" : "Test Connection"}
                  </Button>
                </div>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function platformInitial(platform: SettingsPlatform): string {
  if (platform === "mock") {
    return "M";
  }

  if (platform === "product_hunt") {
    return "PH";
  }

  return platform.slice(0, 1).toUpperCase();
}

function fallbackPhase(platform: SettingsPlatform): PlatformPhase {
  if (platform === "mock" || platform === "reddit" || platform === "product_hunt") {
    return "P0";
  }

  if (platform === "x") {
    return "P1";
  }

  return "P2";
}

function fallbackStatus(platform: SettingsPlatform): CredentialStatus {
  if (platform === "mock") {
    return "available";
  }

  if (platform === "x" || platform === "discord") {
    return "coming_soon";
  }

  return "configured_unverified";
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
  if (status === "available" || status === "configured" || status === "configured_unverified" || status === "valid") {
    return "success";
  }

  if (status === "invalid" || status === "permission_limited") {
    return "danger";
  }

  if (status === "disabled" || status === "missing" || status === "missing_env" || status === "rate_limited") {
    return "warning";
  }

  return "neutral";
}

function platformLabelSafe(platform: SettingsPlatform): string {
  return platform === "mock" ? "Mock" : platformLabel(platform);
}

function envHelpText(platform: SettingsPlatform): string {
  const envCount = REQUIRED_ENV_COUNTS[platform] ?? 0;
  if (envCount === 0) {
    return platform === "mock" ? "无需 .env，始终可用于个人闭环验证。" : "Coming soon，本轮不阻塞。";
  }

  return `需要 ${envCount} 个本地环境变量。`;
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${sanitizeSecretMarkers(error.message)}`;
  }

  return "环境检查失败。";
}

function sanitizeSecretMarkers(value: string): string {
  return value.replace(/\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\b/g, "本地环境变量");
}
