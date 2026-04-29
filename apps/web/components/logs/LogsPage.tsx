"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import {
  formatDateTime,
  formatNumber,
  formatStatusLabel,
  platformLabel,
  truncateText
} from "../../lib/format";
import type { CollectionLog, PaginatedResponse } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

type LogsState =
  | { status: "idle" | "loading" }
  | { status: "ready"; response: PaginatedResponse<CollectionLog> }
  | { status: "error"; error: unknown };

export function LogsPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId");
  const [state, setState] = useState<LogsState>({ status: "idle" });

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
          <p className="pageSubtitle">所选项目的只读采集历史。</p>
        </div>
      </header>

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

function Th({ children }: { children: string }) {
  return <th>{children}</th>;
}
