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

export function DashboardControls({ projectId }: DashboardControlsProps) {
  const router = useRouter();
  const [collectionMode, setCollectionMode] =
    useState<(typeof COLLECTION_MODES)[number]>("mock");
  const [processMode, setProcessMode] =
    useState<NonNullable<ProcessingRequest["mode"]>>("mock");
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
              setCollectionMode(event.target.value as (typeof COLLECTION_MODES)[number])
            }
            value={collectionMode}
          >
            {COLLECTION_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {mode}
              </option>
            ))}
          </select>
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
              setProcessMode(event.target.value as NonNullable<ProcessingRequest["mode"]>)
            }
            value={processMode}
          >
            {PROCESS_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {mode}
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

  return `采集任务 ${response.status}（${response.collector_execution}）：${counters}`;
}

function formatProcessingMessage(response: ProcessingResponse): string {
  return `处理完成（${response.mode}）：本次处理 ${response.processed_in_run} 条，信号总数 ${response.total_signals}。`;
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知前端错误。";
}
