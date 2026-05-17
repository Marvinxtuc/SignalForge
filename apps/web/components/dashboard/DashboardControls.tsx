"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import type { CollectionJobCreateResponse, ProcessingRequest, ProcessingResponse } from "../../lib/types";
import { Button } from "../ui/Button";
import styles from "./Dashboard.module.css";

type DashboardControlsProps = {
  projectId: string;
};

type ActionState =
  | { status: "idle" }
  | { status: "loading"; action: "collect" | "process" }
  | { status: "success"; message: string }
  | { status: "error"; message: string };

const COLLECTION_MODES = ["mock", "reddit", "product_hunt", "p0_real"] as const;
const PROCESS_MODES: Array<NonNullable<ProcessingRequest["mode"]>> = ["mock", "fallback_only"];
type CollectionMode = (typeof COLLECTION_MODES)[number];
type ProcessMode = NonNullable<ProcessingRequest["mode"]>;

const COLLECTION_MODE_LABELS: Record<CollectionMode, string> = {
  mock: "模拟数据",
  reddit: "Reddit（需配置）",
  product_hunt: "Product Hunt（需配置）",
  p0_real: "P0 真实平台（需配置）"
};

const COLLECTION_MODE_HINTS: Record<CollectionMode, string> = {
  mock: "使用本地模拟数据，采集后再运行处理即可生成信号。",
  reddit: "需要 Reddit 环境变量；未配置时会安全跳过，入库为 0，不会产生信号。",
  product_hunt: "需要 Product Hunt 环境变量；未配置时会安全跳过，入库为 0，不会产生信号。",
  p0_real: "会尝试 P0 真实平台；未配置平台环境变量时会安全跳过，入库为 0。"
};

const PROCESS_MODE_LABELS: Record<string, string> = {
  mock: "模拟处理",
  fallback_only: "规则兜底处理"
};

export function DashboardControls({ projectId }: DashboardControlsProps) {
  const router = useRouter();
  const [collectionMode, setCollectionMode] = useState<CollectionMode>("mock");
  const [processMode, setProcessMode] = useState<ProcessMode>("mock");
  const [reprocess, setReprocess] = useState(false);
  const [state, setState] = useState<ActionState>({ status: "idle" });

  async function runCollection() {
    setState({ status: "loading", action: "collect" });

    try {
      const response = await api.collection.collect(projectId, { execution_mode: collectionMode });
      setState({ status: "success", message: formatCollectionMessage(response) });
      router.refresh();
    } catch (error) {
      setState({ status: "error", message: formatActionError(error) });
    }
  }

  async function runProcessing() {
    setState({ status: "loading", action: "process" });

    try {
      const response = await api.processing.run(projectId, {
        mode: processMode,
        reprocess
      });
      setState({ status: "success", message: formatProcessingMessage(response) });
      router.refresh();
    } catch (error) {
      setState({ status: "error", message: formatActionError(error) });
    }
  }

  const isBusy = state.status === "loading";

  return (
    <section className={styles.controlsPanel} aria-labelledby="dashboard-controls-title">
      <div>
        <h2 className={styles.panelTitle} id="dashboard-controls-title">
          运行控制
        </h2>
        <p className={styles.panelMeta}>触发安全采集和本地处理后刷新仪表盘摘要。</p>
      </div>

      <div className={styles.controlsGrid}>
        <label className={styles.controlField}>
          <span>采集模式</span>
          <select
            disabled={isBusy}
            onChange={(event) =>
              setCollectionMode(event.target.value as CollectionMode)
            }
            value={collectionMode}
          >
            {COLLECTION_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {COLLECTION_MODE_LABELS[mode]}
              </option>
            ))}
          </select>
          <small>{COLLECTION_MODE_HINTS[collectionMode]}</small>
        </label>
        <Button
          disabled={isBusy}
          onClick={() => void runCollection()}
          type="button"
          variant="primary"
        >
          {state.status === "loading" && state.action === "collect" ? "采集中" : "运行采集"}
        </Button>

        <label className={styles.controlField}>
          <span>处理模式</span>
          <select
            disabled={isBusy}
            onChange={(event) =>
              setProcessMode(event.target.value as ProcessMode)
            }
            value={processMode}
          >
            {PROCESS_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {PROCESS_MODE_LABELS[mode] ?? mode}
              </option>
            ))}
          </select>
        </label>
        <label className={styles.inlineCheck}>
          <input
            checked={reprocess}
            disabled={isBusy}
            onChange={(event) => setReprocess(event.target.checked)}
            type="checkbox"
          />
          重新处理
        </label>
        <Button disabled={isBusy} onClick={() => void runProcessing()} type="button">
          {state.status === "loading" && state.action === "process" ? "处理中" : "运行处理"}
        </Button>
      </div>

      {state.status === "success" ? <p className={styles.inlineSuccess}>{state.message}</p> : null}
      {state.status === "error" ? (
        <p className={styles.inlineError} role="alert">
          {state.message}
        </p>
      ) : null}
    </section>
  );
}

function formatCollectionMessage(response: CollectionJobCreateResponse): string {
  const log = response.log;
  const counters = log
    ? `采集 ${log.items_collected} / 入库 ${log.items_inserted} / 跳过 ${log.items_skipped}`
    : "暂无日志明细";
  const status = log?.status ?? response.status;
  const statusLabel = collectionStatusLabel(status);
  const modeLabel =
    COLLECTION_MODE_LABELS[response.collector_execution as CollectionMode] ??
    response.collector_execution;
  const zeroInsertHint =
    log && log.items_inserted === 0
      ? "未入库原始数据，因此不会产生信号；请切换到“模拟数据”采集，或先配置真实平台环境变量。"
      : null;
  const disabledHint =
    log && log.status !== "success"
      ? "真实平台当前未完成采集，已按安全策略跳过。"
      : null;
  const detail = [disabledHint, zeroInsertHint].filter(Boolean).join(" ");

  return `采集任务 ${statusLabel}（${modeLabel}）：${counters}${detail ? `。${detail}` : ""}`;
}

function formatProcessingMessage(response: ProcessingResponse): string {
  const modeLabel = PROCESS_MODE_LABELS[response.mode] ?? response.mode;
  const zeroSignalHint =
    response.total_raw_items === 0
      ? "当前没有原始数据，请先运行“模拟数据”采集或完成真实平台配置。"
      : null;

  return `处理完成（${modeLabel}）：本次处理 ${response.processed_in_run} 条，信号总数 ${response.total_signals}。${zeroSignalHint ?? ""}`;
}

function collectionStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    success: "成功",
    disabled: "已跳过",
    missing_env: "缺少配置",
    rate_limited: "限流",
    permission_limited: "权限受限",
    error: "失败"
  };

  return labels[status] ?? status;
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知前端错误。";
}
