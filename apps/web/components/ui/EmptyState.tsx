import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  compact?: boolean;
};

export function EmptyState({ action, compact = false, description, title }: EmptyStateProps) {
  return (
    <section className={`stateBlock${compact ? " stateBlockCompact" : ""}`}>
      <h2 className="stateTitle">{title}</h2>
      {description ? <p className="stateText">{description}</p> : null}
      {action}
    </section>
  );
}
