"use client";

import { useSearchParams } from "next/navigation";
import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import type { CsvReportResponse, MarkdownReportResponse } from "../../lib/types";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";

type ExportState =
  | { status: "idle" }
  | { status: "loading"; format: "markdown" | "csv" }
  | { status: "markdown"; report: MarkdownReportResponse }
  | { status: "csv"; report: CsvReportResponse }
  | { status: "error"; error: unknown };

export function ReportsPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId");
  const [state, setState] = useState<ExportState>({ status: "idle" });

  useEffect(() => {
    setState({ status: "idle" });
  }, [projectId]);

  if (!projectId) {
    return (
      <EmptyState
        description="Select a project to export markdown or csv reports."
        title="No project selected"
      />
    );
  }
  const currentProjectId = projectId;

  async function exportMarkdown() {
    setState({ status: "loading", format: "markdown" });

    try {
      const report = await api.reports.markdown(currentProjectId);
      setState({ status: "markdown", report });
    } catch (error) {
      setState({ status: "error", error });
    }
  }

  async function exportCsv() {
    setState({ status: "loading", format: "csv" });

    try {
      const report = await api.reports.csv(currentProjectId);
      downloadBlob({
        content: report.content,
        contentType: report.content_type || "text/csv;charset=utf-8",
        filename: report.filename || fallbackCsvFilename(currentProjectId)
      });
      setState({ status: "csv", report });
    } catch (error) {
      setState({ status: "error", error });
    }
  }

  function downloadMarkdown() {
    if (state.status !== "markdown") {
      return;
    }

    downloadBlob({
      content: state.report.content,
      contentType: "text/markdown;charset=utf-8",
      filename: fallbackMarkdownFilename(currentProjectId)
    });
  }

  const loadingFormat = state.status === "loading" ? state.format : null;

  return (
    <section style={{ display: "grid", gap: 16 }}>
      <header style={{ display: "grid", gap: 4 }}>
        <p className="sectionLabel">Reports</p>
        <h1 style={{ fontSize: 24, lineHeight: 1.2, margin: 0 }}>Report exports</h1>
        <p className="stateText" style={{ maxWidth: 760 }}>
          Export markdown and csv reports with source_url preserved from the backend response.
        </p>
      </header>

      <section style={panelStyle}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <Button
            disabled={loadingFormat !== null}
            onClick={exportMarkdown}
            type="button"
            variant="primary"
          >
            {loadingFormat === "markdown" ? "Exporting markdown" : "Export markdown"}
          </Button>
          <Button disabled={loadingFormat !== null} onClick={exportCsv} type="button">
            {loadingFormat === "csv" ? "Exporting csv" : "Export csv"}
          </Button>
          <Button
            disabled={state.status !== "markdown" || loadingFormat !== null}
            onClick={downloadMarkdown}
            type="button"
            variant="secondary"
          >
            Download markdown
          </Button>
        </div>
      </section>

      {state.status === "error" ? (
        <ErrorState error={state.error} title="Unable to export report" />
      ) : null}

      {state.status === "markdown" ? (
        <section style={panelStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
            <h2 style={{ fontSize: 16, margin: 0 }}>Markdown preview</h2>
            <span className="selectorMeta">
              Generated {formatDateTime(state.report.generated_at)}
            </span>
          </div>
          <textarea
            aria-label="Markdown preview"
            readOnly
            spellCheck={false}
            style={previewStyle}
            value={state.report.content}
          />
        </section>
      ) : null}

      {state.status === "csv" ? (
        <section style={panelStyle}>
          <h2 style={{ fontSize: 16, margin: 0 }}>CSV export</h2>
          <p className="stateText">
            Downloaded {state.report.filename || fallbackCsvFilename(currentProjectId)}. Generated{" "}
            {formatDateTime(state.report.generated_at)}.
          </p>
          <pre style={csvPreviewStyle}>{state.report.content}</pre>
        </section>
      ) : null}
    </section>
  );
}

function downloadBlob({
  content,
  contentType,
  filename
}: {
  content: string;
  contentType: string;
  filename: string;
}) {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function fallbackCsvFilename(projectId: string): string {
  return `signalforge-report-${projectId}.csv`;
}

function fallbackMarkdownFilename(projectId: string): string {
  return `signalforge-report-${projectId}.md`;
}

const panelStyle: CSSProperties = {
  display: "grid",
  gap: 12,
  border: "1px solid var(--border)",
  borderRadius: 8,
  background: "var(--surface)",
  padding: 16
};

const previewStyle: CSSProperties = {
  minHeight: 360,
  width: "100%",
  resize: "vertical",
  border: "1px solid var(--border-strong)",
  borderRadius: 6,
  color: "var(--text)",
  background: "var(--surface-subtle)",
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  fontSize: 13,
  lineHeight: 1.55,
  padding: 12
};

const csvPreviewStyle: CSSProperties = {
  maxHeight: 260,
  overflow: "auto",
  margin: 0,
  border: "1px solid var(--border-strong)",
  borderRadius: 6,
  background: "var(--surface-subtle)",
  color: "var(--text)",
  fontSize: 12,
  lineHeight: 1.5,
  padding: 12,
  whiteSpace: "pre"
};
