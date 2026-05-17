"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { api } from "../../lib/api";
import { formatDateTime, formatNumber, formatScore } from "../../lib/format";
import { buildAllowedQueryHref } from "../../lib/query";
import type { Opportunity, OpportunityStatus } from "../../lib/types";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { ErrorState } from "../ui/ErrorState";
import { Metric } from "../ui/Metric";
import {
  OPPORTUNITY_STATUSES,
  formatPlatformDistribution,
  isOpportunityStatus,
  opportunityStatusLabel
} from "./opportunityView";

type OpportunityDetailProps = {
  initialOpportunity: Opportunity;
  projectId: string | null;
};

export function OpportunityDetail({ initialOpportunity, projectId }: OpportunityDetailProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [opportunity, setOpportunity] = useState(initialOpportunity);
  const [error, setError] = useState<unknown>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  async function handleStatusChange(nextStatus: OpportunityStatus) {
    setError(null);
    setPendingAction("status");

    try {
      const updated = await api.opportunities.updateStatus(opportunity.id, nextStatus);
      setOpportunity(updated);
      router.refresh();
    } catch (updateError) {
      setError(updateError);
    } finally {
      setPendingAction(null);
    }
  }

  async function handleArchive() {
    setError(null);
    setPendingAction("archive");

    try {
      const updated = await api.opportunities.archive(opportunity.id);
      setOpportunity(updated);
      router.refresh();
    } catch (archiveError) {
      setError(archiveError);
    } finally {
      setPendingAction(null);
    }
  }

  const selectedStatus = isOpportunityStatus(opportunity.status) ? opportunity.status : "new";
  const backHref = buildAllowedQueryHref("/opportunities", searchParams, { projectId });

  return (
    <section className="detailPage">
      <div className="detailHeader">
        <div className="detailTitleBlock">
          <Link className="button buttonGhost buttonSmall" href={backHref}>
            返回看板
          </Link>
          <Badge>{opportunityStatusLabel(opportunity.status)}</Badge>
          <h1 className="detailTitle">{opportunity.title}</h1>
          {opportunity.description ? (
            <p className="detailDescription">{opportunity.description}</p>
          ) : (
            <p className="detailDescription">暂无机会描述。</p>
          )}
        </div>
        <div className="detailActions">
          <select
            aria-label="机会状态"
            className="selectControl"
            disabled={pendingAction !== null}
            onChange={(event) => handleStatusChange(event.target.value as OpportunityStatus)}
            value={selectedStatus}
          >
            {OPPORTUNITY_STATUSES.map((status) => (
              <option key={status} value={status}>
                {opportunityStatusLabel(status)}
              </option>
            ))}
          </select>
          <Button
            disabled={pendingAction !== null || opportunity.status === "archived"}
            onClick={handleArchive}
            variant="secondary"
          >
            {pendingAction === "archive" ? "归档中" : "归档"}
          </Button>
        </div>
      </div>

      {error ? <ErrorState compact error={error} title="无法更新机会" /> : null}

      <section aria-label="机会指标" className="metricGrid">
        <Metric label="机会评分" value={formatScore(opportunity.opportunity_score)} />
        <Metric label="证据数量" value={formatNumber(opportunity.evidence_count)} />
        <Metric label="最近出现" value={formatDateTime(opportunity.last_seen_at)} />
        <Metric label="状态" value={opportunityStatusLabel(opportunity.status)} />
      </section>

      <section aria-labelledby="opportunity-evidence" className="surfacePanel">
        <h2 id="opportunity-evidence" className="opportunityCardTitle">
          证据
        </h2>
        <div className="evidenceGrid">
          <EvidenceItem label="聚类 ID" value={opportunity.cluster_id ?? "不可用"} />
          <EvidenceItem label="证据数量" value={formatNumber(opportunity.evidence_count)} />
          <EvidenceItem
            label="平台分布"
            value={formatPlatformDistribution(opportunity.platform_distribution)}
          />
          <EvidenceItem label="最近出现" value={formatDateTime(opportunity.last_seen_at)} />
        </div>
        <p className="stateText">
          当前机会数据未返回可直接打开的来源证据。
        </p>
      </section>
    </section>
  );
}

function EvidenceItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="compactMeta">
      <p className="compactMetaLabel">{label}</p>
      <p className="compactMetaValue">{value}</p>
    </div>
  );
}
