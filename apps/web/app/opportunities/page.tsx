import { OpportunityBoard } from "../../components/opportunities/OpportunityBoard";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { api } from "../../lib/api";

type SearchParams = Record<string, string | string[] | undefined>;

type OpportunitiesPageProps = {
  searchParams?: Promise<SearchParams>;
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
      <section className="detailPage">
        <header className="pageHeader">
          <div>
            <p className="pageEyebrow">Opportunities</p>
            <h1 className="pageTitle">Opportunity Board</h1>
            <p className="pageSubtitle">
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
