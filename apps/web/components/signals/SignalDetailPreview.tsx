"use client";

import type { Signal } from "../../lib/types";
import {
  formatDateTime,
  formatFeedbackLabel,
  formatScore,
  formatSignalTypeLabel,
  formatStatusLabel,
  platformLabel
} from "../../lib/format";
import { Badge } from "../ui/Badge";
import { EmptyState } from "../ui/EmptyState";
import styles from "./SignalInbox.module.css";

type SignalDetailPreviewProps = {
  signal: Signal | null;
};

export function SignalDetailPreview({ signal }: SignalDetailPreviewProps) {
  if (!signal) {
    return (
      <aside className={styles.detailPreview} aria-label="信号详情预览">
        <EmptyState
          compact
          description="从信号收件箱选择一条信号以查看详情。"
          title="未选择信号"
        />
      </aside>
    );
  }

  return (
    <aside className={styles.detailPreview} aria-label="信号详情预览">
      <div>
        <p className={styles.eyebrow}>详情预览</p>
        <h2 className={styles.detailTitle}>{signal.summary_zh || "未命名信号"}</h2>
      </div>

      <div className={styles.cardMeta}>
        <Badge>{platformLabel(signal.platform)}</Badge>
        <Badge>{formatSignalTypeLabel(signal.signal_type)}</Badge>
        <Badge>痛点 {formatScore(signal.pain_level)}</Badge>
      </div>

      <dl className={styles.detailGrid}>
        <div>
          <dt>信号置信度</dt>
          <dd>{formatScore(signal.signal_confidence)}</dd>
        </div>
        <div>
          <dt>模型置信度</dt>
          <dd>{formatScore(signal.model_confidence)}</dd>
        </div>
        <div>
          <dt>清晰度</dt>
          <dd>{formatScore(signal.clarity_score)}</dd>
        </div>
        <div>
          <dt>紧急度</dt>
          <dd>{formatScore(signal.urgency_score)}</dd>
        </div>
        <div>
          <dt>商业相关性</dt>
          <dd>{formatScore(signal.business_relevance)}</dd>
        </div>
        <div>
          <dt>创建时间</dt>
          <dd>{formatDateTime(signal.created_at)}</dd>
        </div>
        <div>
          <dt>状态</dt>
          <dd>{formatStatusLabel(signal.status)}</dd>
        </div>
        <div>
          <dt>用户反馈</dt>
          <dd>{formatFeedbackLabel(signal.user_feedback)}</dd>
        </div>
      </dl>

      <section className={styles.previewSection}>
        <h3>原文摘录</h3>
        <p>{signal.content_excerpt || "暂无摘录。"}</p>
      </section>

      <section className={styles.previewSection}>
        <h3>建议动作</h3>
        <p>{signal.recommended_action || "暂无建议。"}</p>
      </section>

      <section className={styles.previewSection}>
        <h3>来源</h3>
        {signal.source_url ? (
          <a href={signal.source_url} rel="noopener noreferrer" target="_blank">
            {signal.source_url}
          </a>
        ) : (
          <p>暂无来源。</p>
        )}
      </section>

      {signal.keyword_hits?.length ? (
        <section className={styles.previewSection}>
          <h3>命中关键词</h3>
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
