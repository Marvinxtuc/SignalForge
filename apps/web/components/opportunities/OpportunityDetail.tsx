"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, apiRequest } from "../../lib/api";
import { formatDateTime, formatNumber, formatScore } from "../../lib/format";
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
  const [opportunity, setOpportunity] = useState(initialOpportunity);
  const [error, setError] = useState<unknown>(null);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  async function handleStatusChange(nextStatus: OpportunityStatus) {
    setError(null);
    setPendingAction("status");

    try {
      const updated = await apiRequest<Opportunity>(
        `/api/opportunities/${encodeURIComponent(opportunity.id)}`,
        {
          method: "PUT",
          body: { status: nextStatus }
        }
      );
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
  const backHref = projectId ? `/opportunities?projectId=${encodeURIComponent(projectId)}` : "/opportunities";

  return (
    <section className="detailPage">
      <div className="detailHeader">
        <div className="detailTitleBlock">
          <Link className="button buttonGhost buttonSmall" href={backHref}>
            Back to board
          </Link>
          <Badge>{opportunityStatusLabel(opportunity.status)}</Badge>
          <h1 className="detailTitle">{opportunity.title}</h1>
          {opportunity.description ? (
            <p className="detailDescription">{opportunity.description}</p>
          ) : (
            <p className="detailDescription">No opportunity description available.</p>
          )}
        </div>
        <div className="detailActions">
          <select
            aria-label="Opportunity status"
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
            {pendingAction === "archive" ? "Archiving" : "Archive"}
          </Button>
        </div>
      </div>

      {error ? <ErrorState compact error={error} title="Unable to update opportunity" /> : null}

      <section aria-label="Opportunity metrics" className="metricGrid">
        <Metric label="Score" value={formatScore(opportunity.opportunity_score)} />
        <Metric label="Evidence" value={formatNumber(opportunity.evidence_count)} />
        <Metric label="Last seen" value={formatDateTime(opportunity.last_seen_at)} />
        <Metric label="Status" value={opportunityStatusLabel(opportunity.status)} />
      </section>

      <section aria-labelledby="opportunity-evidence" className="surfacePanel">
        <h2 id="opportunity-evidence" className="opportunityCardTitle">
          Evidence
        </h2>
        <div className="evidenceGrid">
          <EvidenceItem label="Cluster ID" value={opportunity.cluster_id ?? "Unavailable"} />
          <EvidenceItem label="Evidence count" value={formatNumber(opportunity.evidence_count)} />
          <EvidenceItem
            label="Platform distribution"
            value={formatPlatformDistribution(opportunity.platform_distribution)}
          />
          <EvidenceItem label="Last seen" value={formatDateTime(opportunity.last_seen_at)} />
        </div>
        <p className="stateText">
          Source evidence unavailable from current opportunity payload.
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
