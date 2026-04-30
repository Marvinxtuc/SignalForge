"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import type {
  Opportunity,
  ProcessingRequest,
  Signal,
  SignalFeedback,
  SignalListParams,
  SignalStatus
} from "../../lib/types";
import { Button } from "../ui/Button";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { SignalCard } from "./SignalCard";
import { SignalDetailPreview } from "./SignalDetailPreview";
import { SignalFilters, type SignalFilterValues } from "./SignalFilters";
import styles from "./SignalInbox.module.css";

type SignalInboxProps = {
  projectId: string | null;
};

type PendingAction = {
  signalId: string;
  action: string;
} | null;

const DEFAULT_FILTERS: SignalFilterValues = {
  platform: "",
  signalType: "",
  status: "",
  keyword: "",
  minPainLevel: "",
  dateFrom: "",
  dateTo: "",
  highValueOnly: false
};

const PROCESS_MODES: Array<NonNullable<ProcessingRequest["mode"]>> = ["mock", "fallback_only"];

export function SignalInbox({ projectId }: SignalInboxProps) {
  const [filters, setFilters] = useState<SignalFilterValues>(DEFAULT_FILTERS);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<unknown>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [actionErrors, setActionErrors] = useState<Record<string, string>>({});
  const [actionMessages, setActionMessages] = useState<Record<string, string>>({});
  const [processMode, setProcessMode] =
    useState<NonNullable<ProcessingRequest["mode"]>>("mock");
  const [isProcessing, setIsProcessing] = useState(false);
  const [processError, setProcessError] = useState<string | null>(null);
  const [processMessage, setProcessMessage] = useState<string | null>(null);

  const loadSignals = useCallback(async () => {
    if (!projectId) {
      setSignals([]);
      setSelectedSignalId(null);
      return;
    }

    setIsLoading(true);
    setLoadError(null);

    try {
      const response = await api.signals.list(projectId, buildSignalListParams(filters));
      const nextSignals = filters.highValueOnly
        ? response.items.filter((signal) => (signal.signal_confidence ?? 0) >= 60)
        : response.items;

      setSignals(nextSignals);
      setSelectedSignalId((currentId) => {
        if (currentId && nextSignals.some((signal) => signal.id === currentId)) {
          return currentId;
        }

        return nextSignals[0]?.id ?? null;
      });
    } catch (error) {
      setLoadError(error);
      setSignals([]);
      setSelectedSignalId(null);
    } finally {
      setIsLoading(false);
    }
  }, [filters, projectId]);

  useEffect(() => {
    void loadSignals();
  }, [loadSignals]);

  const selectedSignal = useMemo(
    () => signals.find((signal) => signal.id === selectedSignalId) ?? null,
    [selectedSignalId, signals]
  );

  async function updateSignalStatus(signalId: string, status: SignalStatus) {
    await runSignalAction(signalId, `status:${status}`, () => api.signals.updateStatus(signalId, status));
  }

  async function updateSignalFeedback(signalId: string, feedback: SignalFeedback) {
    await runSignalAction(signalId, `feedback:${feedback}`, () =>
      api.signals.updateFeedback(signalId, feedback)
    );
  }

  async function createOpportunity(signalId: string) {
    setPendingAction({ signalId, action: "opportunity:create" });
    setActionErrors((current) => ({ ...current, [signalId]: "" }));
    setActionMessages((current) => ({ ...current, [signalId]: "" }));

    try {
      const opportunity = await api.opportunities.createFromSignal(signalId);
      setActionMessages((current) => ({
        ...current,
        [signalId]: formatOpportunityMessage(opportunity)
      }));
    } catch (error) {
      setActionErrors((current) => ({
        ...current,
        [signalId]: formatActionError(error)
      }));
    } finally {
      setPendingAction(null);
    }
  }

  async function runSignalAction(signalId: string, action: string, request: () => Promise<Signal>) {
    setPendingAction({ signalId, action });
    setActionErrors((current) => ({ ...current, [signalId]: "" }));
    setActionMessages((current) => ({ ...current, [signalId]: "" }));

    try {
      const updatedSignal = await request();
      setSignals((currentSignals) =>
        currentSignals.map((signal) => (signal.id === updatedSignal.id ? updatedSignal : signal))
      );
      setSelectedSignalId(updatedSignal.id);
    } catch (error) {
      setActionErrors((current) => ({
        ...current,
        [signalId]: formatActionError(error)
      }));
    } finally {
      setPendingAction(null);
    }
  }

  async function runProcess() {
    if (!projectId || !PROCESS_MODES.includes(processMode)) {
      return;
    }

    setIsProcessing(true);
    setProcessError(null);
    setProcessMessage(null);

    try {
      const response = await api.processing.run(projectId, { mode: processMode });
      setProcessMessage(
        `处理完成（${response.mode}）：当前共有 ${response.total_signals} 条信号。`
      );
      await loadSignals();
    } catch (error) {
      setProcessError(formatActionError(error));
    } finally {
      setIsProcessing(false);
    }
  }

  if (!projectId) {
    return (
      <EmptyState
        description="请先在项目选择器中选择项目，然后查看信号。"
        title="请选择项目"
      />
    );
  }

  return (
    <section className={styles.inbox} aria-label="信号收件箱">
      <SignalFilters filters={filters} isDisabled={isLoading} onChange={setFilters} />

      <section className={styles.signalList} aria-label="信号列表">
        <div className={styles.listHeader}>
          <div>
            <p className={styles.eyebrow}>信号收件箱</p>
            <h1 className={styles.title}>信号</h1>
          </div>
          <Button disabled={isLoading} onClick={() => void loadSignals()} size="small">
            刷新
          </Button>
        </div>

        <div className={styles.processPanel}>
          <div className={styles.processHeader}>
            <div>
              <p className={styles.fieldLabel}>处理动作</p>
              <p className={styles.processHint}>运行本地 MVP 处理并回填信号 / 机会。</p>
            </div>
            <div className={styles.processControls}>
              <select
                className={styles.input}
                disabled={isProcessing}
                onChange={(event) =>
                  setProcessMode(event.target.value as NonNullable<ProcessingRequest["mode"]>)
                }
                value={processMode}
              >
                <option value="mock">mock</option>
                <option value="fallback_only">fallback_only</option>
              </select>
              <Button
                disabled={isProcessing || !PROCESS_MODES.includes(processMode)}
                onClick={() => void runProcess()}
                size="small"
                variant="primary"
              >
                {isProcessing ? "处理中" : "运行处理"}
              </Button>
            </div>
          </div>
          {processError ? <p className={styles.inlineError}>{processError}</p> : null}
          {processMessage ? <p className={styles.inlineSuccess}>{processMessage}</p> : null}
        </div>

        {isLoading ? <LoadingState label="正在加载信号" /> : null}

        {loadError ? (
          <ErrorState
            action={
              <Button onClick={() => void loadSignals()} size="small" variant="primary">
                重试
              </Button>
            }
            error={loadError}
            title="无法加载信号"
          />
        ) : null}

        {!isLoading && !loadError && signals.length === 0 ? (
          <EmptyState
            description="当前项目和筛选条件下没有返回信号。请使用已批准的本地 MVP 模式运行处理，然后刷新信号收件箱。"
            title="暂无信号"
          />
        ) : null}

        <div className={styles.cards}>
          {signals.map((signal) => (
            <div className={styles.cardStack} key={signal.id}>
              <SignalCard
                actionError={actionErrors[signal.id] ?? null}
                isPending={pendingAction?.signalId === signal.id}
                isSelected={selectedSignalId === signal.id}
                onCreateOpportunity={() => void createOpportunity(signal.id)}
                onFeedback={(feedback) => void updateSignalFeedback(signal.id, feedback)}
                onIgnore={() => void updateSignalStatus(signal.id, "ignored")}
                onSave={() => void updateSignalStatus(signal.id, "saved")}
                onSelect={() => setSelectedSignalId(signal.id)}
                pendingAction={pendingAction?.signalId === signal.id ? pendingAction.action : null}
                signal={signal}
              />
              {actionMessages[signal.id] ? (
                <p className={styles.inlineSuccess}>{actionMessages[signal.id]}</p>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <SignalDetailPreview signal={selectedSignal} />
    </section>
  );
}

function formatOpportunityMessage(opportunity: Opportunity): string {
  return `已生成机会：${opportunity.title}`;
}

function buildSignalListParams(filters: SignalFilterValues): SignalListParams {
  const minPainLevel = filters.highValueOnly ? 70 : parseOptionalNumber(filters.minPainLevel);

  return {
    page_size: 100,
    platform: filters.platform.trim() || undefined,
    signal_type: filters.signalType.trim() || undefined,
    status: filters.status || undefined,
    keyword: filters.keyword.trim() || undefined,
    min_pain_level: minPainLevel,
    date_from: toDateTimeStart(filters.dateFrom),
    date_to: toDateTimeEnd(filters.dateTo)
  };
}

function parseOptionalNumber(value: string): number | undefined {
  const trimmedValue = value.trim();

  if (!trimmedValue) {
    return undefined;
  }

  const parsedValue = Number(trimmedValue);
  return Number.isFinite(parsedValue) ? parsedValue : undefined;
}

function toDateTimeStart(value: string): string | undefined {
  return value ? `${value}T00:00:00.000Z` : undefined;
}

function toDateTimeEnd(value: string): string | undefined {
  return value ? `${value}T23:59:59.999Z` : undefined;
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知前端错误。";
}
