"use client";

import { useSearchParams } from "next/navigation";
import type { CSSProperties, ReactNode } from "react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDateTime, formatNumber, platformLabel, truncateText } from "../../lib/format";
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
        description="Select a project to inspect collection logs."
        title="No project selected"
      />
    );
  }

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <header style={{ display: "grid", gap: 4 }}>
        <p className="sectionLabel">Logs</p>
        <h1 style={{ fontSize: 24, lineHeight: 1.2, margin: 0 }}>Collection logs</h1>
        <p className="stateText" style={{ maxWidth: 760 }}>
          Read-only collection history for the selected project.
        </p>
      </header>

      {state.status === "loading" || state.status === "idle" ? (
        <LoadingState label="Loading collection logs" />
      ) : null}

      {state.status === "error" ? (
        <ErrorState error={state.error} title="Unable to load collection logs" />
      ) : null}

      {state.status === "ready" && state.response.items.length === 0 ? (
        <EmptyState
          compact
          description="No collection log records were returned for this project."
          title="No logs found"
        />
      ) : null}

      {state.status === "ready" && state.response.items.length > 0 ? (
        <div style={{ overflowX: "auto" }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <Th>Status</Th>
                <Th>Platform</Th>
                <Th>Collected</Th>
                <Th>Inserted</Th>
                <Th>Skipped</Th>
                <Th>Error</Th>
                <Th>Rate limit</Th>
                <Th>Reset at</Th>
                <Th>Created at</Th>
              </tr>
            </thead>
            <tbody>
              {state.response.items.map((log) => (
                <tr key={log.id}>
                  <Td>
                    <Badge tone={statusTone(log.status)}>{log.status}</Badge>
                  </Td>
                  <Td>{platformLabel(log.platform)}</Td>
                  <Td>{formatNumber(log.items_collected)}</Td>
                  <Td>{formatNumber(log.items_inserted)}</Td>
                  <Td>{formatNumber(log.items_skipped)}</Td>
                  <Td>{sanitizeErrorMessage(log.error_message)}</Td>
                  <Td>{formatNumber(log.rate_limit_remaining)}</Td>
                  <Td>{formatDateTime(log.rate_limit_reset_at)}</Td>
                  <Td>{formatDateTime(log.created_at)}</Td>
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

  return truncateText(firstReadableLine || "Collection failed. See backend logs for details.", 140);
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

function Th({ children }: { children: ReactNode }) {
  return <th style={headerCellStyle}>{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td style={bodyCellStyle}>{children}</td>;
}

const tableStyle: CSSProperties = {
  width: "100%",
  minWidth: 980,
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
