import type { CSSProperties } from "react";
import { EmptyState } from "../ui/EmptyState";
import type { Opportunity } from "../../lib/types";
import { OpportunityCard } from "./OpportunityCard";
import {
  OPPORTUNITY_STATUSES,
  isOpportunityStatus,
  opportunityStatusLabel
} from "./opportunityView";

type OpportunityBoardProps = {
  opportunities: Opportunity[];
  projectId: string;
};

const boardStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
  gap: 12,
  alignItems: "start"
};

const columnStyle: CSSProperties = {
  display: "grid",
  gap: 10,
  minWidth: 0,
  border: "1px solid var(--border)",
  borderRadius: 8,
  background: "var(--surface-subtle)",
  padding: 10
};

const columnHeaderStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  gap: 8
};

const columnTitleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  fontSize: 13,
  fontWeight: 760
};

const countStyle: CSSProperties = {
  minWidth: 24,
  borderRadius: 999,
  background: "var(--surface-strong)",
  color: "var(--muted-strong)",
  padding: "2px 8px",
  textAlign: "center",
  fontSize: 12,
  fontWeight: 750
};

const cardListStyle: CSSProperties = {
  display: "grid",
  gap: 10
};

export function OpportunityBoard({ opportunities, projectId }: OpportunityBoardProps) {
  const grouped = groupByStatus(opportunities);

  return (
    <section aria-label="Opportunity board" style={boardStyle}>
      {OPPORTUNITY_STATUSES.map((status) => {
        const items = grouped[status];

        return (
          <section aria-labelledby={`opportunity-column-${status}`} key={status} style={columnStyle}>
            <div style={columnHeaderStyle}>
              <h2 id={`opportunity-column-${status}`} style={columnTitleStyle}>
                {opportunityStatusLabel(status)}
              </h2>
              <span aria-label={`${items.length} opportunities`} style={countStyle}>
                {items.length}
              </span>
            </div>
            {items.length === 0 ? (
              <EmptyState
                compact
                description="No opportunities in this status."
                title="Empty column"
              />
            ) : (
              <div style={cardListStyle}>
                {items.map((opportunity) => (
                  <OpportunityCard
                    key={opportunity.id}
                    opportunity={opportunity}
                    projectId={projectId}
                  />
                ))}
              </div>
            )}
          </section>
        );
      })}
    </section>
  );
}

function groupByStatus(opportunities: Opportunity[]): Record<(typeof OPPORTUNITY_STATUSES)[number], Opportunity[]> {
  const grouped = OPPORTUNITY_STATUSES.reduce(
    (accumulator, status) => ({
      ...accumulator,
      [status]: []
    }),
    {} as Record<(typeof OPPORTUNITY_STATUSES)[number], Opportunity[]>
  );

  opportunities.forEach((opportunity) => {
    const status = isOpportunityStatus(opportunity.status) ? opportunity.status : "new";
    grouped[status].push(opportunity);
  });

  return grouped;
}
