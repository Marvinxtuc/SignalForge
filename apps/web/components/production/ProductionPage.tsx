"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import { formatDateTime, formatNumber, formatStatusLabel } from "../../lib/format";
import type {
  ProductionRunCreateRequest,
  ProductionRunListItem,
  ProductionRunMode,
  ProductionRunRead,
  ProductionRunStatus
} from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";

type PageState =
  | { status: "idle" | "loading" }
  | { status: "ready"; runStatus: ProductionRunStatus; runs: ProductionRunListItem[] }
  | { status: "error"; error: unknown };

type RunActionState =
  | { status: "idle" }
  | { status: "running"; message: string }
  | { status: "success"; message: string }
  | { status: "error"; message: string };

type ApprovalKey = keyof ProductionRunCreateRequest["approvals"];

const RUN_MODES: ProductionRunMode[] = ["mock", "preview", "production"];
const COLLECTION_MODES = ["mock", "reddit", "product_hunt", "p0_real"] as const;
const PROCESSING_MODES = ["mock", "fallback_only", "real_llm", "real_embedding"] as const;
const CONFIRMATION_TEXT = "APPROVE";

const APPROVAL_LABELS: Array<{ key: ApprovalKey; label: string; detail: string }> = [
  {
    key: "real_platform_read",
    label: "允许真实平台读取",
    detail: "允许本次 run 尝试真实平台 read/smoke，仍受后端 env gate 约束。"
  },
  {
    key: "real_platform_write",
    label: "允许真实平台写入",
    detail: "当前前端不会执行写入；此项仅记录显式批准并保留门禁状态。"
  },
  {
    key: "real_llm",
    label: "允许真实 LLM 调用",
    detail: "选择 real_llm 处理模式时才会尝试；后端当前默认拒绝。"
  },
  {
    key: "real_embedding",
    label: "允许真实 embedding 调用",
    detail: "选择 real_embedding 处理模式时才会尝试；后端当前默认拒绝。"
  }
];

const INITIAL_APPROVALS: ProductionRunCreateRequest["approvals"] = {
  real_platform_read: false,
  real_platform_write: false,
  real_llm: false,
  real_embedding: false,
  confirmation_text: ""
};

export function ProductionPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId");
  const [pageState, setPageState] = useState<PageState>({ status: "idle" });
  const [actionState, setActionState] = useState<RunActionState>({ status: "idle" });
  const [mode, setMode] = useState<ProductionRunMode>("mock");
  const [collectionMode, setCollectionMode] =
    useState<(typeof COLLECTION_MODES)[number]>("mock");
  const [processingMode, setProcessingMode] =
    useState<(typeof PROCESSING_MODES)[number]>("fallback_only");
  const [reprocess, setReprocess] = useState(false);
  const [approvals, setApprovals] =
    useState<ProductionRunCreateRequest["approvals"]>(INITIAL_APPROVALS);
  const [localRuns, setLocalRuns] = useState<ProductionRunListItem[]>([]);

  const explicitApprovalRequired = useMemo(
    () =>
      mode !== "mock" ||
      collectionMode !== "mock" ||
      processingMode.startsWith("real_") ||
      approvals.real_platform_write ||
      approvals.real_llm ||
      approvals.real_embedding,
    [approvals, collectionMode, mode, processingMode]
  );

  const canRun =
    Boolean(projectId) &&
    actionState.status !== "running" &&
    (!explicitApprovalRequired || approvals.confirmation_text === CONFIRMATION_TEXT) &&
    (!processingMode.startsWith("real_llm") || approvals.real_llm) &&
    (!processingMode.startsWith("real_embedding") || approvals.real_embedding) &&
    (collectionMode === "mock" || approvals.real_platform_read);

  useEffect(() => {
    if (!projectId) {
      setPageState({ status: "idle" });
      return;
    }

    void loadStatus(projectId);
  }, [projectId]);

  async function loadStatus(currentProjectId: string) {
    setPageState({ status: "loading" });

    try {
      const [runStatus, persistedRuns] = await Promise.all([
        api.production.status(currentProjectId),
        api.production.listRuns(currentProjectId)
      ]);
      setPageState({
        status: "ready",
        runStatus,
        runs: mergeRuns(localRuns, persistedRuns)
      });
    } catch (error) {
      setPageState({ status: "error", error });
    }
  }

  async function createRun() {
    if (!projectId || !canRun) {
      return;
    }

    const createdAt = new Date().toISOString();
    const localRunId = crypto.randomUUID();
    const runRequest: ProductionRunCreateRequest = {
      mode,
      collection_execution_mode: collectionMode,
      processing_mode: processingMode,
      reprocess,
      approvals
    };

    upsertLocalRun({
      id: localRunId,
      project_id: projectId,
      created_at: createdAt,
      state: "collect",
      status: "running",
      mode,
      collection_job_id: null,
      processing_mode: processingMode,
      items_inserted: null,
      total_signals: null,
      error_message: null
    });

    setActionState({ status: "running", message: "正在创建 production lifecycle run。" });

    try {
      const createdRun = await api.production.createRun(projectId, runRequest);
      const listItem = productionRunReadToListItem(createdRun, mode);

      upsertLocalRun(listItem);

      setActionState({
        status: createdRun.status === "success" ? "success" : "error",
        message: formatRunResult(createdRun)
      });
    } catch (error) {
      const message = formatActionError(error);
      upsertLocalRun({
        id: localRunId,
        project_id: projectId,
        created_at: createdAt,
        state: "closeout",
        status: "failed",
        mode,
        collection_job_id: null,
        processing_mode: processingMode,
        items_inserted: null,
        total_signals: null,
        error_message: message
      });
      setActionState({ status: "error", message });
    } finally {
      await loadStatus(projectId);
    }
  }

  function upsertLocalRun(nextRun: ProductionRunListItem) {
    setLocalRuns((current) => {
      const others = current.filter((run) => run.id !== nextRun.id);
      return [nextRun, ...others].slice(0, 20);
    });
  }

  function updateApproval(key: ApprovalKey, value: boolean | string) {
    setApprovals((current) => ({ ...current, [key]: value }));
  }

  if (!projectId) {
    return <EmptyState description="请选择项目后再创建本地生产 run。" title="请选择项目" />;
  }

  return (
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">生产运行</p>
          <h1 className="pageTitle">Mac mini owner-only lifecycle</h1>
          <p className="pageSubtitle">
            本页只使用 same-origin API proxy 和现有后端接口。真实平台写入与真实模型调用必须逐次勾选并确认。
          </p>
        </div>
        <Button disabled={pageState.status === "loading"} onClick={() => void loadStatus(projectId)}>
          刷新状态
        </Button>
      </header>

      <section className="productionGrid">
        <section className="surfacePanel" aria-labelledby="run-create-title">
          <div>
            <h2 className="opportunityCardTitle" id="run-create-title">
              Run Creation
            </h2>
            <p className="selectorMeta">先 collect，再 process；失败会停在 closeout 并显示后端返回原因。</p>
          </div>

          <div className="productionControlGrid">
            <label className="compactField">
              <span>Run mode</span>
              <select
                className="selectControl"
                onChange={(event) => setMode(event.target.value as ProductionRunMode)}
                value={mode}
              >
                {RUN_MODES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="compactField">
              <span>Collect</span>
              <select
                className="selectControl"
                onChange={(event) =>
                  setCollectionMode(event.target.value as (typeof COLLECTION_MODES)[number])
                }
                value={collectionMode}
              >
                {COLLECTION_MODES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="compactField">
              <span>Process</span>
              <select
                className="selectControl"
                onChange={(event) =>
                  setProcessingMode(event.target.value as (typeof PROCESSING_MODES)[number])
                }
                value={processingMode}
              >
                {PROCESSING_MODES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="checkboxRow productionCheckbox">
              <input
                checked={reprocess}
                onChange={(event) => setReprocess(event.target.checked)}
                type="checkbox"
              />
              <span>Reprocess existing raw items</span>
            </label>
          </div>

          <div className="approvalList" aria-label="run approvals">
            {APPROVAL_LABELS.map((item) => (
              <label className="checkboxRow approvalItem" key={item.key}>
                <input
                  checked={Boolean(approvals[item.key])}
                  onChange={(event) => updateApproval(item.key, event.target.checked)}
                  type="checkbox"
                />
                <span>
                  <strong>{item.label}</strong>
                  <small>{item.detail}</small>
                </span>
              </label>
            ))}
          </div>

          <label className="formField">
            <span>Explicit confirmation</span>
            <input
              onChange={(event) => updateApproval("confirmation_text", event.target.value)}
              placeholder={explicitApprovalRequired ? CONFIRMATION_TEXT : "mock 模式无需确认"}
              value={approvals.confirmation_text}
            />
            <small>非 mock 或任何真实批准项需要输入 {CONFIRMATION_TEXT}。</small>
          </label>

          <div className="detailActions">
            <Button disabled={!canRun} onClick={() => void createRun()} type="button" variant="primary">
              {actionState.status === "running" ? "运行中" : "创建并运行"}
            </Button>
            <Badge tone={canRun ? "success" : "warning"}>
              {canRun ? "Gate ready" : "等待批准条件"}
            </Badge>
          </div>
          {actionState.status === "running" ? <p className="selectorMeta">{actionState.message}</p> : null}
          {actionState.status === "success" ? <p className="inlineSuccess">{actionState.message}</p> : null}
          {actionState.status === "error" ? (
            <p className="inlineError" role="alert">
              {actionState.message}
            </p>
          ) : null}
        </section>

        <section className="surfacePanel" aria-labelledby="run-status-title">
          <div>
            <h2 className="opportunityCardTitle" id="run-status-title">
              Current Status
            </h2>
            <p className="selectorMeta">来自 processing summary 与最近 collection logs。</p>
          </div>
          {pageState.status === "loading" || pageState.status === "idle" ? (
            <LoadingState label="正在加载生产状态" />
          ) : null}
          {pageState.status === "error" ? (
            <ErrorState compact error={pageState.error} title="无法加载生产状态" />
          ) : null}
          {pageState.status === "ready" ? (
            <>
              <div className="metricGrid">
                <Metric label="Raw processed" value={pageState.runStatus.processing_summary.processed_raw_items} />
                <Metric label="Signals" value={pageState.runStatus.processing_summary.total_signals} />
                <Metric label="Embeddings" value={pageState.runStatus.processing_summary.embedding_count} />
                <Metric label="Opportunities" value={pageState.runStatus.processing_summary.opportunity_count} />
              </div>
              <p className="selectorMeta">最近检查 {formatDateTime(pageState.runStatus.checked_at)}</p>
            </>
          ) : null}
        </section>
      </section>

      {pageState.status === "ready" && pageState.runs.length > 0 ? (
        <div className="dataTableWrap">
          <table className="dataTable">
            <thead>
              <tr>
                <Th>状态</Th>
                <Th>阶段</Th>
                <Th>模式</Th>
                <Th>采集 Job</Th>
                <Th>处理模式</Th>
                <Th>入库</Th>
                <Th>信号</Th>
                <Th>错误</Th>
                <Th>创建时间</Th>
              </tr>
            </thead>
            <tbody>
              {pageState.runs.map((run) => (
                <tr key={run.id}>
                  <td>
                    <Badge tone={run.status === "failed" ? "danger" : "success"}>
                      {formatStatusLabel(run.status)}
                    </Badge>
                  </td>
                  <td>{run.state}</td>
                  <td>{run.mode}</td>
                  <td>{run.collection_job_id ?? "-"}</td>
                  <td>{run.processing_mode ?? "-"}</td>
                  <td>{formatNumber(run.items_inserted)}</td>
                  <td>{formatNumber(run.total_signals)}</td>
                  <td>{run.error_message ?? "-"}</td>
                  <td>{formatDateTime(run.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric">
      <p className="metricLabel">{label}</p>
      <p className="metricValue">{formatNumber(value)}</p>
    </div>
  );
}

function Th({ children }: { children: string }) {
  return <th scope="col">{children}</th>;
}

function mergeRuns(localRuns: ProductionRunListItem[], persistedRuns: ProductionRunListItem[]) {
  const seen = new Set<string>();
  return [...localRuns, ...persistedRuns].filter((run) => {
    if (seen.has(run.id)) {
      return false;
    }

    seen.add(run.id);
    return true;
  });
}

function productionRunReadToListItem(
  run: ProductionRunRead,
  displayMode: ProductionRunMode
): ProductionRunListItem {
  const collectionSummary = asRecord(run.result_summary.collection);
  const processingSummary = asRecord(run.result_summary.processing);

  return {
    id: run.id,
    project_id: run.project_id ?? "",
    created_at: run.created_at ?? run.started_at ?? new Date().toISOString(),
    state: formatProductionRunStage(run.stage),
    status: run.status,
    mode: displayMode,
    collection_job_id: typeof collectionSummary.job_id === "string" ? collectionSummary.job_id : null,
    processing_mode: run.processing_mode,
    items_inserted: numberValue(collectionSummary.items_inserted),
    total_signals: numberValue(processingSummary.total_signals),
    error_message: run.error_summary
  };
}

function formatRunResult(run: ProductionRunRead): string {
  if (run.status !== "success") {
    return `${run.status}: ${run.error_summary ?? "后端 preflight 或 lifecycle gate 未通过。"}`;
  }

  const processingSummary = asRecord(run.result_summary.processing);
  return `run 完成：信号 ${formatNumber(numberValue(processingSummary.total_signals))} 条，状态 ${run.stage}。`;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

function formatProductionRunStage(runStage: string): ProductionRunListItem["state"] {
  if (runStage === "collect" || runStage === "process" || runStage === "review" || runStage === "report") {
    return runStage;
  }

  return runStage === "closeout" ? "closeout" : "review";
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知生产运行错误。";
}
