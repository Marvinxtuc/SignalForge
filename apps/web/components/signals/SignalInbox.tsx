"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import type { ProcessingRequest, Signal, SignalFeedback, SignalListParams, SignalStatus } from "../../lib/types";
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

  async function runSignalAction(signalId: string, action: string, request: () => Promise<Signal>) {
    setPendingAction({ signalId, action });
    setActionErrors((current) => ({ ...current, [signalId]: "" }));

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
        `Process completed in ${response.mode}: ${response.total_signals} signals available.`
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
        description="Use the project selector to choose a project before reviewing signals."
        title="Select a project"
      />
    );
  }

  return (
    <section className={styles.inbox} aria-label="Signal Inbox">
      <SignalFilters filters={filters} isDisabled={isLoading} onChange={setFilters} />

      <section className={styles.signalList} aria-label="Signals">
        <div className={styles.listHeader}>
          <div>
            <p className={styles.eyebrow}>Signal Inbox</p>
            <h1 className={styles.title}>Signals</h1>
          </div>
          <Button disabled={isLoading} onClick={() => void loadSignals()} size="small">
            Refresh
          </Button>
        </div>

        {isLoading ? <LoadingState label="Loading signals" /> : null}

        {loadError ? (
          <ErrorState
            action={
              <Button onClick={() => void loadSignals()} size="small" variant="primary">
                Retry
              </Button>
            }
            error={loadError}
            title="Unable to load signals"
          />
        ) : null}

        {!isLoading && !loadError && signals.length === 0 ? (
          <EmptyState
            action={
              <div className={styles.processPanel}>
                <label className={styles.fieldLabel} htmlFor="process-mode">
                  Process mode
                </label>
                <div className={styles.processControls}>
                  <select
                    className={styles.input}
                    disabled={isProcessing}
                    id="process-mode"
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
                    variant="primary"
                  >
                    {isProcessing ? "Processing" : "Run Process"}
                  </Button>
                </div>
                {processError ? <p className={styles.inlineError}>{processError}</p> : null}
                {processMessage ? <p className={styles.inlineSuccess}>{processMessage}</p> : null}
              </div>
            }
            description="No signals returned for this project and filter set. Run Process with an approved local MVP mode, then refresh the inbox."
            title="No signals yet"
          />
        ) : null}

        <div className={styles.cards}>
          {signals.map((signal) => (
            <SignalCard
              actionError={actionErrors[signal.id] ?? null}
              isPending={pendingAction?.signalId === signal.id}
              isSelected={selectedSignalId === signal.id}
              key={signal.id}
              onFeedback={(feedback) => void updateSignalFeedback(signal.id, feedback)}
              onIgnore={() => void updateSignalStatus(signal.id, "ignored")}
              onSave={() => void updateSignalStatus(signal.id, "saved")}
              onSelect={() => setSelectedSignalId(signal.id)}
              pendingAction={pendingAction?.signalId === signal.id ? pendingAction.action : null}
              signal={signal}
            />
          ))}
        </div>
      </section>

      <SignalDetailPreview signal={selectedSignal} />
    </section>
  );
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

  return "Unexpected frontend error.";
}
