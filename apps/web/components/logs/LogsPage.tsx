"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import {
  formatDateTime,
  formatNumber,
  formatStatusLabel,
  platformLabel,
  truncateText
} from "../../lib/format";
import type { CollectionJobCreateResponse, CollectionLog, PaginatedResponse } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

type LogsState =
  | { status: "idle" | "loading" }
  | { status: "ready"; response: PaginatedResponse<CollectionLog> }
  | { status: "error"; error: unknown };

type CollectionActionState =
  | { status: "idle" }
  | { status: "running" }
  | { status: "success"; message: string }
  | { status: "error"; message: string };

const COLLECTION_MODES = ["mock", "reddit", "product_hunt", "p0_real"] as const;

export function LogsPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId");
  const [state, setState] = useState<LogsState>({ status: "idle" });
  const [collectionMode, setCollectionMode] =
    useState<(typeof COLLECTION_MODES)[number]>("mock");
  const [actionState, setActionState] = useState<CollectionActionState>({ status: "idle" });

  async function loadLogs(currentProjectId: string) {
    setState({ status: "loading" });

    try {
      const response = await api.collection.listLogs(currentProjectId, { page_size: 50 });
      setState({ status: "ready", response });
    } catch (error) {
      setState({ status: "error", error });
    }
  }

  async function runCollection() {
    if (!projectId) {
      return;
    }

    setActionState({ status: "running" });

    try {
      const response = await api.collection.collect(projectId, { execution_mode: collectionMode });
      setActionState({ status: "success", message: formatCollectionMessage(response) });
      await loadLogs(projectId);
    } catch (error) {
      setActionState({ status: "error", message: formatActionError(error) });
    }
  }

  useEffect(() => {
    if (!projectId) {
      setState({ status: "idle" });
      return;
    }

    let active = true;
    setState({ status: "loading" });

    api.collection
      .listLogs(projectId, { page_size: 50 })
      .then((response) => {
        if (active) {
          setState({ status: "ready", response });
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
  }, [projectId]);

  if (!projectId) {
    return (
      <EmptyState
        description="请选择项目以查看采集日志。"
        title="请选择项目"
      />
    );
  }

  return (
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">运行日志</p>
          <h1 className="pageTitle">采集日志</h1>
          <p className="pageSubtitle">所选项目的采集历史和安全采集控制。</p>
        </div>
      </header>

      <section className="surfacePanel">
        <div className="detailActions">
          <label className="compactField">
            <span>采集模式</span>
            <select
              className="selectControl"
              disabled={actionState.status === "running"}
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
            disabled={actionState.status === "running"}
            onClick={() => void runCollection()}
            type="button"
            variant="primary"
          >
            {actionState.status === "running" ? "采集中" : "运行采集"}
          </Button>
          <Button
            disabled={state.status === "loading"}
            onClick={() => void loadLogs(projectId)}
            type="button"
          >
            刷新日志
          </Button>
        </div>
        {actionState.status === "success" ? (
          <p className="inlineSuccess">{actionState.message}</p>
        ) : null}
        {actionState.status === "error" ? (
          <p className="inlineError" role="alert">
            {actionState.message}
          </p>
        ) : null}
      </section>

      {state.status === "loading" || state.status === "idle" ? (
        <LoadingState label="正在加载采集日志" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState error={state.error} title="无法加载采集日志" />
      ) : null}

      {state.status === "ready" && state.response.items.length === 0 ? (
        <EmptyState
          compact
          description="当前项目暂无采集日志记录。"
          title="未找到日志"
        />
      ) : null}

      {state.status === "ready" && state.response.items.length > 0 ? (
        <div className="dataTableWrap">
          <table className="dataTable">
            <thead>
              <tr>
                <Th>状态</Th>
                <Th>平台</Th>
                <Th>采集数量</Th>
                <Th>入库数量</Th>
                <Th>跳过数量</Th>
                <Th>错误信息</Th>
                <Th>速率限制</Th>
                <Th>重置时间</Th>
                <Th>创建时间</Th>
              </tr>
            </thead>
            <tbody>
              {state.response.items.map((log) => (
                <tr key={log.id}>
                  <td>
                    <Badge tone={statusTone(log.status)}>{formatStatusLabel(log.status)}</Badge>
                  </td>
                  <td>{platformLabel(log.platform)}</td>
                  <td>{formatNumber(log.items_collected)}</td>
                  <td>{formatNumber(log.items_inserted)}</td>
                  <td>{formatNumber(log.items_skipped)}</td>
                  <td>{sanitizeErrorMessage(log.error_message)}</td>
                  <td>{formatNumber(log.rate_limit_remaining)}</td>
                  <td>{formatDateTime(log.rate_limit_reset_at)}</td>
                  <td>{formatDateTime(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function sanitizeErrorMessage(value: string | null): string {
  if (!value) {
    return "-";
  }

  const normalized = value.replace(/\r\n/g, "\n").trim();
  if (!normalized) {
    return "-";
  }

  const tracebackIndex = normalized.search(/(^|\n)traceback\b/i);
  const withoutTraceback =
    tracebackIndex >= 0 ? normalized.slice(0, tracebackIndex).trim() : normalized;
  const firstReadableLine = withoutTraceback
    .split("\n")
    .map((line) => line.trim())
    .find((line) => line && !/^\s*(file ".*", line \d+|at\s+\S+)/i.test(line));

  return truncateText(firstReadableLine || "采集失败。详情请查看后端日志。", 140);
}

function statusTone(status: string): "neutral" | "success" | "warning" | "danger" {
  const normalized = status.toLowerCase();

  if (["success", "completed", "ok"].includes(normalized)) {
    return "success";
  }

  if (["failed", "error"].includes(normalized)) {
    return "danger";
  }

  if (["partial", "rate_limited", "warning"].includes(normalized)) {
    return "warning";
  }

  return "neutral";
}

function formatCollectionMessage(response: CollectionJobCreateResponse): string {
  const log = response.log;
  const detail = log
    ? `采集 ${formatNumber(log.items_collected)} / 入库 ${formatNumber(log.items_inserted)} / 跳过 ${formatNumber(log.items_skipped)}`
    : "暂无日志明细";

  return `采集任务 ${formatStatusLabel(response.status)}（${response.collector_execution}）：${detail}`;
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知前端错误。";
}

function Th({ children }: { children: string }) {
  return <th>{children}</th>;
}
