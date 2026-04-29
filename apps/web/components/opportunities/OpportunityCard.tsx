import Link from "next/link";
import { Badge } from "../ui/Badge";
import { formatDateTime, formatNumber, formatScore } from "../../lib/format";
import type { Opportunity } from "../../lib/types";
import { formatPlatformDistribution, opportunityStatusLabel } from "./opportunityView";

type OpportunityCardProps = {
  opportunity: Opportunity;
  projectId: string;
};

export function OpportunityCard({ opportunity, projectId }: OpportunityCardProps) {
  const detailHref = `/opportunities/${encodeURIComponent(opportunity.id)}?projectId=${encodeURIComponent(
    projectId
  )}`;

  return (
    <article className="opportunityCard">
      <div className="opportunityCardHeader">
        <h3 className="opportunityCardTitle">{opportunity.title}</h3>
        <Badge>{opportunityStatusLabel(opportunity.status)}</Badge>
      </div>
      <div className="opportunityMetaGrid">
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
    <div className="compactMeta">
      <p className="compactMetaLabel">{label}</p>
      <p className="compactMetaValue">{value}</p>
    </div>
  );
}
