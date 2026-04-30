"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import type { CsvReportResponse, MarkdownReportResponse, ReportRequest } from "../../lib/types";
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
  const [reportOptions, setReportOptions] = useState({
    days: "7",
    minPainLevel: "70",
    topClustersLimit: "10",
    opportunitiesLimit: "10"
  });
  const [lastExportPath, setLastExportPath] = useState<string | null>(null);

  useEffect(() => {
    setState({ status: "idle" });
    setLastExportPath(null);
  }, [projectId]);

  if (!projectId) {
    return (
      <EmptyState
        description="请选择项目以导出 Markdown 或 CSV 报告。"
        title="请选择项目"
      />
    );
  }
  const currentProjectId = projectId;

  async function exportMarkdown() {
    setState({ status: "loading", format: "markdown" });

    try {
      const report = await api.reports.markdown(currentProjectId, buildReportRequest(reportOptions));
      setLastExportPath(exportPath(fallbackMarkdownFilename(currentProjectId)));
      setState({ status: "markdown", report });
    } catch (error) {
      setState({ status: "error", error });
    }
  }

  async function exportCsv() {
    setState({ status: "loading", format: "csv" });

    try {
      const report = await api.reports.csv(currentProjectId, buildReportRequest(reportOptions));
      const filename = report.filename || fallbackCsvFilename(currentProjectId);
      downloadBlob({
        content: report.content,
        contentType: report.content_type || "text/csv;charset=utf-8",
        filename
      });
      setLastExportPath(exportPath(filename));
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
    setLastExportPath(exportPath(fallbackMarkdownFilename(currentProjectId)));
  }

  const loadingFormat = state.status === "loading" ? state.format : null;

  return (
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">报告导出</p>
          <h1 className="pageTitle">报告导出</h1>
          <p className="pageSubtitle">
            导出 Markdown 和 CSV 报告，并保留后端返回的 source_url。
          </p>
        </div>
      </header>

      <section className="surfacePanel">
        <div className="reportOptionsGrid">
          <label className="compactField">
            <span>天数</span>
            <input
              className="selectControl"
              min="1"
              onChange={(event) =>
                setReportOptions((current) => ({ ...current, days: event.target.value }))
              }
              type="number"
              value={reportOptions.days}
            />
          </label>
          <label className="compactField">
            <span>最低痛点分</span>
            <input
              className="selectControl"
              min="0"
              max="100"
              onChange={(event) =>
                setReportOptions((current) => ({ ...current, minPainLevel: event.target.value }))
              }
              type="number"
              value={reportOptions.minPainLevel}
            />
          </label>
          <label className="compactField">
            <span>聚类上限</span>
            <input
              className="selectControl"
              min="1"
              onChange={(event) =>
                setReportOptions((current) => ({
                  ...current,
                  topClustersLimit: event.target.value
                }))
              }
              type="number"
              value={reportOptions.topClustersLimit}
            />
          </label>
          <label className="compactField">
            <span>机会上限</span>
            <input
              className="selectControl"
              min="1"
              onChange={(event) =>
                setReportOptions((current) => ({
                  ...current,
                  opportunitiesLimit: event.target.value
                }))
              }
              type="number"
              value={reportOptions.opportunitiesLimit}
            />
          </label>
        </div>
        <div className="detailActions">
          <Button
            disabled={loadingFormat !== null}
            onClick={exportMarkdown}
            type="button"
            variant="primary"
          >
            {loadingFormat === "markdown" ? "正在导出 Markdown" : "Markdown 导出"}
          </Button>
          <Button disabled={loadingFormat !== null} onClick={exportCsv} type="button">
            {loadingFormat === "csv" ? "正在导出 CSV" : "CSV 导出"}
          </Button>
          <Button
            disabled={state.status !== "markdown" || loadingFormat !== null}
            onClick={downloadMarkdown}
            type="button"
            variant="secondary"
          >
            下载 Markdown
          </Button>
        </div>
        <p className="selectorMeta">
          导出路径：{lastExportPath ?? exportPath(fallbackCsvFilename(currentProjectId))}
        </p>
      </section>

      {state.status === "error" ? (
        <ErrorState error={state.error} title="无法导出报告" />
      ) : null}

      {state.status === "markdown" ? (
        <section className="surfacePanel">
          <div className="pageHeader">
            <h2 className="opportunityCardTitle">Markdown 预览</h2>
            <span className="selectorMeta">
              生成时间 {formatDateTime(state.report.generated_at)}
            </span>
          </div>
          <textarea
            aria-label="Markdown 预览"
            readOnly
            spellCheck={false}
            className="reportsPreview"
            value={state.report.content}
          />
        </section>
      ) : null}

      {state.status === "csv" ? (
        <section className="surfacePanel">
          <h2 className="opportunityCardTitle">CSV 导出</h2>
          <p className="stateText">
            已下载 {state.report.filename || fallbackCsvFilename(currentProjectId)}。生成时间{" "}
            {formatDateTime(state.report.generated_at)}。
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

function buildReportRequest(options: {
  days: string;
  minPainLevel: string;
  topClustersLimit: string;
  opportunitiesLimit: string;
}): ReportRequest {
  return {
    days: parseOptionalPositiveInt(options.days),
    min_pain_level: parseOptionalPositiveInt(options.minPainLevel),
    top_clusters_limit: parseOptionalPositiveInt(options.topClustersLimit),
    opportunities_limit: parseOptionalPositiveInt(options.opportunitiesLimit)
  };
}

function parseOptionalPositiveInt(value: string): number | undefined {
  const trimmed = value.trim();

  if (!trimmed) {
    return undefined;
  }

  const parsed = Number(trimmed);

  if (!Number.isInteger(parsed) || parsed < 0) {
    return undefined;
  }

  return parsed;
}

function exportPath(filename: string): string {
  return `浏览器下载目录/${filename}`;
}

function fallbackCsvFilename(projectId: string): string {
  return `signalforge-report-${projectId}.csv`;
}

function fallbackMarkdownFilename(projectId: string): string {
  return `signalforge-report-${projectId}.md`;
}
