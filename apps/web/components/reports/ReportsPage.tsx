"use client";

import { useSearchParams } from "next/navigation";
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
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">Reports</p>
          <h1 className="pageTitle">Report exports</h1>
          <p className="pageSubtitle">
            Export markdown and csv reports with source_url preserved from the backend response.
          </p>
        </div>
      </header>

      <section className="surfacePanel">
        <div className="detailActions">
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
        <section className="surfacePanel">
          <div className="pageHeader">
            <h2 className="opportunityCardTitle">Markdown preview</h2>
            <span className="selectorMeta">
              Generated {formatDateTime(state.report.generated_at)}
            </span>
          </div>
          <textarea
            aria-label="Markdown preview"
            readOnly
            spellCheck={false}
            className="reportsPreview"
            value={state.report.content}
          />
        </section>
      ) : null}

      {state.status === "csv" ? (
        <section className="surfacePanel">
          <h2 className="opportunityCardTitle">CSV export</h2>
          <p className="stateText">
            Downloaded {state.report.filename || fallbackCsvFilename(currentProjectId)}. Generated{" "}
            {formatDateTime(state.report.generated_at)}.
          </p>
          <pre className="csvPreview">{state.report.content}</pre>
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
