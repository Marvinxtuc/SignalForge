"use client";

import type { Signal, SignalFeedback } from "../../lib/types";
import { formatDateTime, formatScore, platformLabel, truncateText } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import styles from "./SignalInbox.module.css";

type SignalCardProps = {
  actionError: string | null;
  isPending: boolean;
  isSelected: boolean;
  pendingAction: string | null;
  signal: Signal;
  onFeedback: (feedback: SignalFeedback) => void;
  onIgnore: () => void;
  onSave: () => void;
  onSelect: () => void;
};

const FEEDBACK_ACTIONS: Array<{ value: SignalFeedback; label: string }> = [
  { value: "valuable", label: "Valuable" },
  { value: "not_valuable", label: "Not Valuable" },
  { value: "wrong_type", label: "Wrong Type" },
  { value: "ignored", label: "Feedback Ignore" }
];

export function SignalCard({
  actionError,
  isPending,
  isSelected,
  onFeedback,
  onIgnore,
  onSave,
  onSelect,
  pendingAction,
  signal
}: SignalCardProps) {
  const highValue = isHighValueSignal(signal);
  const sourceDisabled = !signal.source_url;
  const cardClasses = [
    styles.signalCard,
    isSelected ? styles.selectedSignal : "",
    highValue ? `${styles.highValueSignal} high-value-signal` : ""
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <article className={cardClasses} aria-label="Signal card">
      <button className={styles.cardBodyButton} onClick={onSelect} type="button">
        <div className={styles.cardMeta}>
          <Badge>{platformLabel(signal.platform)}</Badge>
          <Badge>{signal.signal_type || "Unknown type"}</Badge>
          <Badge tone={painTone(signal.pain_level)}>Pain {formatScore(signal.pain_level)}</Badge>
          {highValue ? <Badge tone="success">High Value</Badge> : null}
        </div>

        <div className={styles.cardTitleRow}>
          <h2 className={styles.cardTitle}>{signal.summary_zh || "Untitled signal"}</h2>
          <span className={styles.scoreText}>Confidence {formatScore(signal.signal_confidence)}</span>
        </div>

        <p className={styles.excerpt}>{truncateText(signal.content_excerpt, 220)}</p>

        {signal.keyword_hits?.length ? (
          <div className={styles.keywordRow} aria-label="Keyword hits">
            {signal.keyword_hits.slice(0, 6).map((keyword) => (
              <span className={styles.keyword} key={keyword}>
                {keyword}
              </span>
            ))}
          </div>
        ) : null}

        <p className={styles.cardFooter}>
          Created {formatDateTime(signal.created_at)} · Status {signal.status}
          {signal.user_feedback ? ` · Feedback ${signal.user_feedback}` : ""}
        </p>
      </button>

      <div className={styles.actionBar}>
        {sourceDisabled ? (
          <span className={styles.disabledLink} aria-disabled="true">
            Open Source
          </span>
        ) : (
          <a
            className={styles.sourceLink}
            href={signal.source_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            Open Source
          </a>
        )}
        <Button disabled={isPending} onClick={onSave} size="small" variant="secondary">
          {pendingAction === "status:saved" ? "Saving" : "Save"}
        </Button>
        <Button disabled={isPending} onClick={onIgnore} size="small" variant="ghost">
          {pendingAction === "status:ignored" ? "Ignoring" : "Ignore"}
        </Button>
      </div>

      <div className={styles.feedbackBar} aria-label="feedback actions">
        <span className={styles.feedbackLabel}>feedback</span>
        {FEEDBACK_ACTIONS.map((action) => (
          <Button
            disabled={isPending}
            key={action.value}
            onClick={() => onFeedback(action.value)}
            size="small"
            variant="ghost"
          >
            {pendingAction === `feedback:${action.value}` ? "Updating" : action.label}
          </Button>
        ))}
      </div>

      {actionError ? (
        <p className={styles.inlineError} role="alert">
          {actionError}
        </p>
      ) : null}
    </article>
  );
}

function isHighValueSignal(signal: Signal): boolean {
  return (signal.pain_level ?? 0) >= 70 && (signal.signal_confidence ?? 0) >= 60;
}

function painTone(value: number | null): "neutral" | "success" | "warning" | "danger" {
  if (value === null) {
    return "neutral";
  }

  if (value >= 80) {
    return "danger";
  }

  if (value >= 60) {
    return "warning";
  }

  return "neutral";
}
