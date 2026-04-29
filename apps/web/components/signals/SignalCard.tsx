"use client";

import type { Signal, SignalFeedback } from "../../lib/types";
import {
  formatDateTime,
  formatFeedbackLabel,
  formatScore,
  formatSignalTypeLabel,
  formatStatusLabel,
  platformLabel,
  truncateText
} from "../../lib/format";
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
  { value: "valuable", label: "有价值" },
  { value: "not_valuable", label: "无价值" },
  { value: "wrong_type", label: "类型错误" },
  { value: "ignored", label: "忽略反馈" }
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
    <article className={cardClasses} aria-label="信号卡片">
      <button className={styles.cardBodyButton} onClick={onSelect} type="button">
        <div className={styles.cardMeta}>
          <Badge>{platformLabel(signal.platform)}</Badge>
          <Badge>{formatSignalTypeLabel(signal.signal_type)}</Badge>
          <Badge tone={painTone(signal.pain_level)}>痛点 {formatScore(signal.pain_level)}</Badge>
          {highValue ? <Badge tone="warning">高价值</Badge> : null}
        </div>

        <div className={styles.cardTitleRow}>
          <h2 className={styles.cardTitle}>{signal.summary_zh || "未命名信号"}</h2>
          <span className={styles.scoreText}>置信度 {formatScore(signal.signal_confidence)}</span>
        </div>

        <p className={styles.excerpt}>{truncateText(signal.content_excerpt, 220)}</p>

        {signal.keyword_hits?.length ? (
          <div className={styles.keywordRow} aria-label="命中关键词">
            {signal.keyword_hits.slice(0, 6).map((keyword) => (
              <span className={styles.keyword} key={keyword}>
                {keyword}
              </span>
            ))}
          </div>
        ) : null}

        <p className={styles.cardFooter}>
          创建时间 {formatDateTime(signal.created_at)} · 状态 {formatStatusLabel(signal.status)}
          {signal.user_feedback ? ` · 反馈 ${formatFeedbackLabel(signal.user_feedback)}` : ""}
        </p>
      </button>

      <div className={styles.actionBar}>
        {sourceDisabled ? (
          <span className={styles.disabledLink} aria-disabled="true">
            打开来源
          </span>
        ) : (
          <a
            className={styles.sourceLink}
            href={signal.source_url}
            rel="noopener noreferrer"
            target="_blank"
          >
            打开来源
          </a>
        )}
        <Button disabled={isPending} onClick={onSave} size="small" variant="secondary">
          {pendingAction === "status:saved" ? "保存中" : "保存"}
        </Button>
        <Button disabled={isPending} onClick={onIgnore} size="small" variant="ghost">
          {pendingAction === "status:ignored" ? "忽略中" : "忽略"}
        </Button>
      </div>

      <div className={styles.feedbackBar} aria-label="反馈操作">
        <span className={styles.feedbackLabel}>反馈</span>
        {FEEDBACK_ACTIONS.map((action) => (
          <Button
            disabled={isPending}
            key={action.value}
            onClick={() => onFeedback(action.value)}
            size="small"
            variant="ghost"
          >
            {pendingAction === `feedback:${action.value}` ? "更新中" : action.label}
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
