"use client";

import type { Signal } from "../../lib/types";
import { formatDateTime, formatScore, platformLabel } from "../../lib/format";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import styles from "./SignalInbox.module.css";

type SignalDetailPreviewProps = {
  signal: Signal | null;
};

export function SignalDetailPreview({ signal }: SignalDetailPreviewProps) {
  if (!signal) {
    return (
      <aside className={styles.detailPreview} aria-label="Signal detail preview">
        <EmptyState
          compact
          description="Select a signal from the inbox to inspect its detail."
          title="No signal selected"
        />
      </aside>
    );
  }

  return (
    <aside className={styles.detailPreview} aria-label="Signal detail preview">
      <div>
        <p className={styles.eyebrow}>Detail Preview</p>
        <h2 className={styles.detailTitle}>{signal.summary_zh || "Untitled signal"}</h2>
      </div>

      <div className={styles.cardMeta}>
        <Badge>{platformLabel(signal.platform)}</Badge>
        <Badge>{signal.signal_type || "Unknown type"}</Badge>
        <Badge>Pain {formatScore(signal.pain_level)}</Badge>
      </div>

      <dl className={styles.detailGrid}>
        <div>
          <dt>Signal confidence</dt>
          <dd>{formatScore(signal.signal_confidence)}</dd>
        </div>
        <div>
          <dt>Model confidence</dt>
          <dd>{formatScore(signal.model_confidence)}</dd>
        </div>
        <div>
          <dt>Clarity</dt>
          <dd>{formatScore(signal.clarity_score)}</dd>
        </div>
        <div>
          <dt>Urgency</dt>
          <dd>{formatScore(signal.urgency_score)}</dd>
        </div>
        <div>
          <dt>Business relevance</dt>
          <dd>{formatScore(signal.business_relevance)}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{formatDateTime(signal.created_at)}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{signal.status}</dd>
        </div>
        <div>
          <dt>User feedback</dt>
          <dd>{signal.user_feedback || "-"}</dd>
        </div>
      </dl>

      <section className={styles.previewSection}>
        <h3>Content excerpt</h3>
        <p>{signal.content_excerpt || "No excerpt available."}</p>
      </section>

      <section className={styles.previewSection}>
        <h3>Recommended action</h3>
        <p>{signal.recommended_action || "No recommendation available."}</p>
      </section>

      {signal.keyword_hits?.length ? (
        <section className={styles.previewSection}>
          <h3>Keyword hits</h3>
          <div className={styles.keywordRow}>
            {signal.keyword_hits.map((keyword) => (
              <span className={styles.keyword} key={keyword}>
                {keyword}
              </span>
            ))}
          </div>
        </section>
      ) : null}
    </aside>
  );
}
