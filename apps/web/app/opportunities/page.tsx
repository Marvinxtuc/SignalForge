import type { CSSProperties } from "react";
import { OpportunityBoard } from "../../components/opportunities/OpportunityBoard";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { api } from "../../lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

type OpportunitiesPageProps = {
  searchParams?: Promise<SearchParams>;
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

const titleStyle: CSSProperties = {
  margin: 0,
  color: "var(--text)",
  fontSize: 24,
  fontWeight: 800,
  lineHeight: 1.2
};

const subtitleStyle: CSSProperties = {
  margin: "6px 0 0",
  color: "var(--muted)",
  lineHeight: 1.5
};

export default async function OpportunitiesPage({ searchParams }: OpportunitiesPageProps) {
  const resolvedSearchParams: SearchParams = searchParams ? await searchParams : {};
  const projectId = getSingleSearchParam(resolvedSearchParams.projectId);

  if (!projectId) {
    return (
      <EmptyState
        description="Select a project from the sidebar to load project opportunities."
        title="No project selected"
      />
    );
  }

  try {
    const response = await api.opportunities.list(projectId, { page_size: 100 });

    return (
      <section style={pageStyle}>
        <header style={headerStyle}>
          <div>
            <h1 style={titleStyle}>Opportunity Board</h1>
            <p style={subtitleStyle}>
              Grouped by status for project {projectId}. Showing {response.items.length} of{" "}
              {response.total} opportunities.
            </p>
          </div>
        </header>
        {response.items.length === 0 ? (
          <EmptyState
            description="No opportunities returned by the backend for this project."
            title="No opportunities"
          />
        ) : (
          <OpportunityBoard opportunities={response.items} projectId={projectId} />
        )}
      </section>
    );
  } catch (error) {
    return <ErrorState error={error} title="Unable to load opportunities" />;
  }
}

function getSingleSearchParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
}
