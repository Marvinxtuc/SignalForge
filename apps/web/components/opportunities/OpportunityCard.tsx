"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { formatDateTime, formatNumber, formatScore } from "../../lib/format";
import { buildAllowedQueryHref } from "../../lib/query";
import type { Opportunity, OpportunityStatus } from "../../lib/types";
import {
  OPPORTUNITY_STATUSES,
  formatPlatformDistribution,
  isOpportunityStatus,
  opportunityStatusLabel
} from "./opportunityView";

type OpportunityCardProps = {
  opportunity: Opportunity;
  projectId: string;
};

export function OpportunityCard({ opportunity, projectId }: OpportunityCardProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const detailHref = buildAllowedQueryHref(
    `/opportunities/${encodeURIComponent(opportunity.id)}`,
    searchParams,
    { projectId }
  );
  const selectedStatus = isOpportunityStatus(opportunity.status) ? opportunity.status : "new";

  async function updateStatus(status: OpportunityStatus) {
    setPendingAction("status");
    setError(null);

    try {
      await api.opportunities.updateStatus(opportunity.id, status);
      router.refresh();
    } catch (updateError) {
      setError(formatActionError(updateError));
    } finally {
      setPendingAction(null);
    }
  }

  async function archiveOpportunity() {
    setPendingAction("archive");
    setError(null);

    try {
      await api.opportunities.archive(opportunity.id);
      router.refresh();
    } catch (archiveError) {
      setError(formatActionError(archiveError));
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <article className="opportunityCard">
      <div className="opportunityCardHeader">
        <h3 className="opportunityCardTitle">{opportunity.title}</h3>
        <Badge>{opportunityStatusLabel(opportunity.status)}</Badge>
      </div>
      <div className="opportunityMetaGrid">
        <MetaItem label="机会评分" value={formatScore(opportunity.opportunity_score)} />
        <MetaItem label="证据数量" value={formatNumber(opportunity.evidence_count)} />
        <MetaItem label="最近出现" value={formatDateTime(opportunity.last_seen_at)} />
        <MetaItem label="状态" value={opportunityStatusLabel(opportunity.status)} />
      </div>
      <MetaItem
        label="平台分布"
        value={formatPlatformDistribution(opportunity.platform_distribution)}
      />
      <div className="opportunityCardActions">
        <select
          aria-label="机会状态"
          className="selectControl"
          disabled={pendingAction !== null}
          onChange={(event) => void updateStatus(event.target.value as OpportunityStatus)}
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
          onClick={() => void archiveOpportunity()}
          size="small"
          type="button"
          variant="ghost"
        >
          {pendingAction === "archive" ? "归档中" : "归档"}
        </Button>
        <Link className="button buttonSecondary buttonSmall" href={detailHref}>
          查看详情
        </Link>
      </div>
      {error ? (
        <p className="inlineError" role="alert">
          {error}
        </p>
      ) : null}
    </article>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="compactMeta">
      <p className="compactMetaLabel">{label}</p>
      <p className="compactMetaValue">{value}</p>
    </div>
  );
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知前端错误。";
}
