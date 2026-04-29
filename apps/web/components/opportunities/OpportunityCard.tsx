import Link from "next/link";
import type { CSSProperties } from "react";
import { Badge } from "../ui/Badge";
import { formatDateTime, formatNumber, formatScore } from "../../lib/format";
import type { Opportunity } from "../../lib/types";
import { formatPlatformDistribution, opportunityStatusLabel } from "./opportunityView";

type OpportunityCardProps = {
  opportunity: Opportunity;
  projectId: string;
};

const cardStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  border: "1px solid var(--border)",
  borderRadius: 8,
  background: "var(--surface)",
  padding: 12,
  boxShadow: "var(--shadow)"
};

const headerStyle: CSSProperties = {
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "space-between",
  gap: 10
};

const titleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  fontSize: 14,
  fontWeight: 760,
  lineHeight: 1.35
};

const metaGridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: 8
};

const metaItemStyle: CSSProperties = {
  display: "grid",
  gap: 2,
  minWidth: 0
};

const metaLabelStyle: CSSProperties = {
  margin: 0,
  color: "var(--muted)",
  fontSize: 11,
  fontWeight: 700,
  textTransform: "uppercase"
};

const metaValueStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  overflowWrap: "anywhere"
};

export function OpportunityCard({ opportunity, projectId }: OpportunityCardProps) {
  const detailHref = `/opportunities/${encodeURIComponent(opportunity.id)}?projectId=${encodeURIComponent(
    projectId
  )}`;

  return (
    <article style={cardStyle}>
      <div style={headerStyle}>
        <h3 style={titleStyle}>{opportunity.title}</h3>
        <Badge>{opportunityStatusLabel(opportunity.status)}</Badge>
      </div>
      <div style={metaGridStyle}>
        <MetaItem label="Score" value={formatScore(opportunity.opportunity_score)} />
        <MetaItem label="Evidence" value={formatNumber(opportunity.evidence_count)} />
        <MetaItem label="Last seen" value={formatDateTime(opportunity.last_seen_at)} />
        <MetaItem label="Status" value={opportunityStatusLabel(opportunity.status)} />
      </div>
      <MetaItem
        label="Platforms"
        value={formatPlatformDistribution(opportunity.platform_distribution)}
      />
      <Link className="button buttonSecondary buttonSmall" href={detailHref}>
        Open detail
      </Link>
    </article>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div style={metaItemStyle}>
      <p style={metaLabelStyle}>{label}</p>
      <p style={metaValueStyle}>{value}</p>
    </div>
  );
}
