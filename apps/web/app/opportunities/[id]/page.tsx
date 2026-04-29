import { OpportunityDetail } from "../../../components/opportunities/OpportunityDetail";
import { ErrorState } from "../../../components/ui/ErrorState";
import { api } from "../../../lib/api";

type RouteParams = {
  id: string;
};

type SearchParams = Record<string, string | string[] | undefined>;

type OpportunityDetailPageProps = {
  params: Promise<RouteParams>;
  searchParams?: Promise<SearchParams>;
};

export default async function OpportunityDetailPage({
  params,
  searchParams
}: OpportunityDetailPageProps) {
  const resolvedParams = await Promise.resolve(params);
  const resolvedSearchParams: SearchParams = searchParams ? await searchParams : {};
  const projectId = getSingleSearchParam(resolvedSearchParams.projectId);

  try {
    const opportunity = await api.opportunities.get(resolvedParams.id);

    return <OpportunityDetail initialOpportunity={opportunity} projectId={projectId} />;
  } catch (error) {
    return <ErrorState error={error} title="Unable to load opportunity detail" />;
  }
}

function getSingleSearchParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
}
