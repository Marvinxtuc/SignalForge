"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { CSSProperties } from "react";
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

const pageStyle: CSSProperties = {
  display: "grid",
  gap: 16
};

const headerStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 16,
  flexWrap: "wrap"
};

const titleBlockStyle: CSSProperties = {
  display: "grid",
  gap: 8,
  minWidth: 0
};

const titleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  fontSize: 24,
  fontWeight: 800,
  lineHeight: 1.2
};

const descriptionStyle: CSSProperties = {
  margin: 0,
  maxWidth: 820,
  color: "var(--muted-strong)",
  lineHeight: 1.55
};

const actionsStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 8,
  flexWrap: "wrap"
};

const metricsStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
  gap: 12
};

const sectionStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  border: "1px solid var(--border)",
  borderRadius: 8,
  background: "var(--surface)",
  padding: 14
};

const sectionTitleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  fontSize: 15,
  fontWeight: 760
};

const evidenceGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  gap: 10
};

const evidenceItemStyle: CSSProperties = {
  display: "grid",
  gap: 3,
  minWidth: 0
};

const labelStyle: CSSProperties = {
  margin: 0,
  color: "var(--muted)",
  fontSize: 12,
  fontWeight: 700
};

const valueStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  overflowWrap: "anywhere"
};

const mutedStyle: CSSProperties = {
  margin: 0,
  color: "var(--muted)",
  lineHeight: 1.5
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
    <section style={pageStyle}>
      <div style={headerStyle}>
        <div style={titleBlockStyle}>
          <Link className="button buttonGhost buttonSmall" href={backHref}>
            Back to board
          </Link>
          <Badge>{opportunityStatusLabel(opportunity.status)}</Badge>
          <h1 style={titleStyle}>{opportunity.title}</h1>
          {opportunity.description ? (
            <p style={descriptionStyle}>{opportunity.description}</p>
          ) : (
            <p style={descriptionStyle}>No opportunity description available.</p>
          )}
        </div>
        <div style={actionsStyle}>
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

      <section aria-label="Opportunity metrics" style={metricsStyle}>
        <Metric label="Score" value={formatScore(opportunity.opportunity_score)} />
        <Metric label="Evidence" value={formatNumber(opportunity.evidence_count)} />
        <Metric label="Last seen" value={formatDateTime(opportunity.last_seen_at)} />
        <Metric label="Status" value={opportunityStatusLabel(opportunity.status)} />
      </section>

      <section aria-labelledby="opportunity-evidence" style={sectionStyle}>
        <h2 id="opportunity-evidence" style={sectionTitleStyle}>
          Evidence
        </h2>
        <div style={evidenceGridStyle}>
          <EvidenceItem label="Cluster ID" value={opportunity.cluster_id ?? "Unavailable"} />
          <EvidenceItem label="Evidence count" value={formatNumber(opportunity.evidence_count)} />
          <EvidenceItem
            label="Platform distribution"
            value={formatPlatformDistribution(opportunity.platform_distribution)}
          />
          <EvidenceItem label="Last seen" value={formatDateTime(opportunity.last_seen_at)} />
        </div>
        <p style={mutedStyle}>
          Source evidence unavailable from current opportunity payload.
        </p>
      </section>
    </section>
  );
}

function EvidenceItem({ label, value }: { label: string; value: string }) {
  return (
    <div style={evidenceItemStyle}>
      <p style={labelStyle}>{label}</p>
      <p style={valueStyle}>{value}</p>
    </div>
  );
}
