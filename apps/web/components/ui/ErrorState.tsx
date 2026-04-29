import type { ReactNode } from "react";
import { ApiClientError } from "../../lib/api";

type ErrorStateProps = {
  error: unknown;
  title?: string;
  action?: ReactNode;
  compact?: boolean;
};

export function ErrorState({
  action,
  compact = false,
  error,
  title = "Unable to load data"
}: ErrorStateProps) {
  const message =
    error instanceof ApiClientError
      ? `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`
      : "Unexpected frontend error.";

  return (
    <section className={`stateBlock errorBlock${compact ? " stateBlockCompact" : ""}`} role="alert">
      <h2 className="stateTitle">{title}</h2>
      <p className="stateText">{message}</p>
      {action}
    </section>
  );
}
