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

export function OpportunityBoard({ opportunities, projectId }: OpportunityBoardProps) {
  const grouped = groupByStatus(opportunities);

  return (
    <section aria-label="Opportunity board" className="opportunityBoard">
      {OPPORTUNITY_STATUSES.map((status) => {
        const items = grouped[status];

        return (
          <section
            aria-labelledby={`opportunity-column-${status}`}
            className="opportunityColumn"
            key={status}
          >
            <div className="opportunityColumnHeader">
              <h2 id={`opportunity-column-${status}`} className="opportunityColumnTitle">
                {opportunityStatusLabel(status)}
              </h2>
              <span aria-label={`${items.length} opportunities`} className="opportunityCount">
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
              <div className="opportunityCardList">
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
