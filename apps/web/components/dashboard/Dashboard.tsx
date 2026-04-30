import type { ReactNode } from "react";
import { api, ApiClientError } from "../../lib/api";
import {
  formatDateTime,
  formatNumber,
  formatPercent,
  formatScore,
  formatStatusLabel,
  platformLabel
} from "../../lib/format";
import type {
  CollectionLog,
  Opportunity,
  PlatformName,
  PlatformStatus,
  ProcessingSummary
} from "../../lib/types";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { Metric } from "../ui/Metric";
import { DashboardControls } from "./DashboardControls";
import styles from "./Dashboard.module.css";

type DashboardProps = {
  projectId: string | null;
};

type DashboardData = {
  todaySignalCount: number;
  processingSummary: ProcessingSummary | null;
  opportunities: Opportunity[];
  platforms: PlatformStatus[];
  collectionLogs: CollectionLog[];
  errors: string[];
};

type DashboardBadgeTone = "neutral" | "success" | "warning" | "danger";

const PLATFORM_ORDER: PlatformName[] = ["reddit", "product_hunt", "x", "discord"];

export async function Dashboard({ projectId }: DashboardProps) {
  if (!projectId) {
    return (
      <div className={styles.page}>
        <PageHeader />
        <EmptyState
          description="请先在侧边栏选择项目，以加载信号质量摘要、机会、平台和最近处理状态。"
          title="请选择项目"
        />
      </div>
    );
  }

  const data = await loadDashboardData(projectId);

  return (
    <div className={styles.page}>
      <PageHeader errors={data.errors} />
      <DashboardControls projectId={projectId} />
      <div className={styles.grid}>
        <TodaySignalsPanel count={data.todaySignalCount} />
        <HighValuePanel summary={data.processingSummary} />
        <TopOpportunitiesPanel opportunities={data.opportunities} />
        <PlatformStatusPanel platforms={data.platforms} />
        <RecentStatusPanel logs={data.collectionLogs} summary={data.processingSummary} />
      </div>
    </div>
  );
}

function PageHeader({ errors = [] }: { errors?: string[] }) {
  return (
    <header className={styles.header}>
      <div className={styles.titleBlock}>
        <p className={styles.eyebrow}>仪表盘</p>
        <h1 className={styles.title}>信号质量摘要</h1>
        <p className={styles.subtitle}>
          汇总高价值占比、重点机会、平台状态以及最近采集 / 处理状态。
        </p>
      </div>
      {errors.length > 0 ? (
        <Badge title={errors.join("; ")} tone="warning">
          部分数据
        </Badge>
      ) : (
        <Badge tone="success">API 在线</Badge>
      )}
    </header>
  );
}

function TodaySignalsPanel({ count }: { count: number }) {
  return (
    <section className={`${styles.panel} ${styles.span3}`} aria-labelledby="today-signals-title">
      <PanelHeader
        id="today-signals-title"
        meta="本地当天新增"
        title="今日新增信号"
        value={<Badge tone="neutral">信号</Badge>}
      />
      <p className={styles.largeValue}>{formatNumber(count)}</p>
    </section>
  );
}

function HighValuePanel({ summary }: { summary: ProcessingSummary | null }) {
  const highValueCount = summary?.high_value_signals ?? 0;
  const highValueRatio = summary?.high_value_ratio ?? 0;
  const boundedRatio = Math.max(0, Math.min(1, highValueRatio));

  return (
    <section className={`${styles.panel} ${styles.span5}`} aria-labelledby="high-value-title">
      <PanelHeader
        id="high-value-title"
        meta="信号质量门"
        title="高价值信号"
        value={<Badge tone={highValueCount > 0 ? "success" : "neutral"}>{formatPercent(highValueRatio)}</Badge>}
      />
      <div>
        <p className={styles.largeValue}>{formatNumber(highValueCount)}</p>
        <div className={styles.qualityBar} aria-label={`高价值占比 ${formatPercent(highValueRatio)}`}>
          <div className={styles.qualityFill} style={{ width: `${Math.round(boundedRatio * 100)}%` }} />
        </div>
      </div>
      <div className={styles.metricRow}>
        <Metric
          detail="已识别需求信号"
          label="信号总数"
          value={formatNumber(summary?.total_signals ?? 0)}
        />
        <Metric
          detail="已分类原始项"
          label="已处理"
          value={formatNumber(summary?.processed_raw_items ?? 0)}
        />
        <Metric
          detail="被过滤 / 噪声"
          label="噪声占比"
          value={formatPercent(summary?.noise_ratio ?? 0)}
        />
      </div>
    </section>
  );
}

function TopOpportunitiesPanel({ opportunities }: { opportunities: Opportunity[] }) {
  return (
    <section className={`${styles.panel} ${styles.span7}`} aria-labelledby="top-opportunities-title">
      <PanelHeader
        id="top-opportunities-title"
        meta="按机会评分排序"
        title="重点机会"
        value={<Badge tone="neutral">显示 {formatNumber(opportunities.length)} 个</Badge>}
      />
      {opportunities.length === 0 ? (
        <p className={styles.emptyText}>当前项目暂无机会。</p>
      ) : (
        <ul className={styles.list}>
          {opportunities.map((opportunity) => (
            <li className={styles.opportunityItem} key={opportunity.id}>
              <div>
                <p className={styles.itemTitle}>{opportunity.title}</p>
                <div className={styles.itemMeta}>
                  <Badge tone="neutral">{formatNumber(opportunity.evidence_count)} 条证据</Badge>
                  <Badge tone={opportunityStatusTone(opportunity.status)}>
                    {formatStatusLabel(opportunity.status)}
                  </Badge>
                </div>
              </div>
              <span className={styles.score}>{formatScore(opportunity.opportunity_score)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function PlatformStatusPanel({ platforms }: { platforms: PlatformStatus[] }) {
  const byPlatform = new Map(platforms.map((platform) => [platform.platform, platform]));

  return (
    <section className={`${styles.panel} ${styles.span4}`} aria-labelledby="platform-status-title">
      <PanelHeader
        id="platform-status-title"
        meta="MVP 平台就绪状态"
        title="平台状态"
        value={<Badge tone="neutral">4 个平台</Badge>}
      />
      <div className={styles.platformGrid}>
        {PLATFORM_ORDER.map((platformName) => {
          const platform = byPlatform.get(platformName);
          const status = platform?.status ?? "missing";

          return (
            <article className={styles.platformItem} key={platformName}>
              <p className={styles.platformName}>{platformLabel(platformName)}</p>
              <div className={styles.platformDetail}>
                <Badge tone={credentialStatusTone(status)}>{formatStatusLabel(status)}</Badge>
                <Badge tone={platform?.enabled_for_mvp ? "success" : "neutral"}>
                  {platform?.enabled_for_mvp ? "MVP 已启用" : "MVP 未启用"}
                </Badge>
                {platform ? <Badge tone="neutral">{platform.phase}</Badge> : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function RecentStatusPanel({
  logs,
  summary
}: {
  logs: CollectionLog[];
  summary: ProcessingSummary | null;
}) {
  return (
    <section className={`${styles.panel} ${styles.span8}`} aria-labelledby="recent-status-title">
      <PanelHeader
        id="recent-status-title"
        meta="采集日志和处理摘要"
        title="最近运行状态"
        value={<Badge tone={summary ? "success" : "warning"}>{summary ? "摘要就绪" : "暂无摘要"}</Badge>}
      />
      <div className={styles.statusLayout}>
        <div>
          {logs.length === 0 ? (
            <p className={styles.emptyText}>当前项目暂无最近采集日志。</p>
          ) : (
            <ul className={styles.list}>
              {logs.map((log) => (
                <li className={styles.logItem} key={log.id}>
                  <div className={styles.logTopline}>
                    <p className={styles.logTitle}>{platformLabel(log.platform)}</p>
                    <Badge tone={collectionStatusTone(log.status)}>{formatStatusLabel(log.status)}</Badge>
                    <span className={styles.logMeta}>{formatDateTime(log.created_at)}</span>
                  </div>
                  <p className={styles.logMeta}>
                    采集 {formatNumber(log.items_collected)} / 入库 {formatNumber(log.items_inserted)} /{" "}
                    跳过 {formatNumber(log.items_skipped)}
                  </p>
                  {log.error_message ? <p className={styles.logMeta}>错误：{log.error_message}</p> : null}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className={styles.compactMetrics}>
          <Metric
            detail="后端原始项库存"
            label="原始项"
            value={formatNumber(summary?.total_raw_items ?? 0)}
          />
          <Metric
            detail="机会聚类"
            label="聚类"
            value={formatNumber(summary?.cluster_count ?? 0)}
          />
          <Metric
            detail="LLM JSON 解析失败"
            label="JSON 失败"
            value={formatNumber(summary?.llm_json_failure_count ?? 0)}
          />
        </div>
      </div>
    </section>
  );
}

function PanelHeader({
  id,
  meta,
  title,
  value
}: {
  id: string;
  meta: string;
  title: string;
  value?: ReactNode;
}) {
  return (
    <div className={styles.panelHeader}>
      <div>
        <h2 className={styles.panelTitle} id={id}>
          {title}
        </h2>
        <p className={styles.panelMeta}>{meta}</p>
      </div>
      {value}
    </div>
  );
}

async function loadDashboardData(projectId: string): Promise<DashboardData> {
  const todayStartIso = getTodayStartIso();

  const [todaySignals, processingSummary, opportunities, platforms, collectionLogs] =
    await Promise.allSettled([
      api.signals.list(projectId, { date_from: todayStartIso, page_size: 1 }),
      api.processing.summary(projectId),
      api.opportunities.list(projectId, { page_size: 5 }),
      api.settings.platforms(),
      api.collection.listLogs(projectId, { page_size: 5 })
    ]);

  const errors = [
    resultError(todaySignals, "今日信号"),
    resultError(processingSummary, "处理摘要"),
    resultError(opportunities, "机会"),
    resultError(platforms, "平台设置"),
    resultError(collectionLogs, "采集日志")
  ].filter((error): error is string => Boolean(error));

  return {
    todaySignalCount: todaySignals.status === "fulfilled" ? todaySignals.value.total : 0,
    processingSummary: processingSummary.status === "fulfilled" ? processingSummary.value : null,
    opportunities:
      opportunities.status === "fulfilled"
        ? [...opportunities.value.items].sort(
            (left, right) => (right.opportunity_score ?? 0) - (left.opportunity_score ?? 0)
          )
        : [],
    platforms: platforms.status === "fulfilled" ? platforms.value.platforms : [],
    collectionLogs: collectionLogs.status === "fulfilled" ? collectionLogs.value.items : [],
    errors
  };
}

function getTodayStartIso(): string {
  const start = new Date();
  start.setHours(0, 0, 0, 0);
  return start.toISOString();
}

function resultError<T>(result: PromiseSettledResult<T>, label: string): string | null {
  if (result.status === "fulfilled") {
    return null;
  }

  if (result.reason instanceof ApiClientError) {
    return `${label}: ${result.reason.code}`;
  }

  return `${label}: 不可用`;
}

function opportunityStatusTone(status: string): DashboardBadgeTone {
  if (status === "build_candidate" || status === "content_candidate" || status === "validating") {
    return "success";
  }

  if (status === "archived") {
    return "neutral";
  }

  return "warning";
}

function credentialStatusTone(status: string): DashboardBadgeTone {
  if (status === "configured") {
    return "success";
  }

  if (status === "missing" || status === "disabled") {
    return "neutral";
  }

  return "warning";
}

function collectionStatusTone(status: string): DashboardBadgeTone {
  if (status === "success" || status === "completed") {
    return "success";
  }

  if (status === "failed" || status === "error") {
    return "danger";
  }

  return "warning";
}
