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
        description="请先在侧边栏选择项目，以加载项目机会。"
        title="请选择项目"
      />
    );
  }

  try {
    const response = await api.opportunities.list(projectId, { page_size: 100 });

    return (
      <section className="detailPage">
        <header className="pageHeader">
          <div>
            <p className="pageEyebrow">机会</p>
            <h1 className="pageTitle">机会看板</h1>
            <p className="pageSubtitle">
              按状态分组展示项目 {projectId} 的机会。当前显示 {response.items.length} /{" "}
              {response.total} 个机会。
            </p>
          </div>
        </header>
        {response.items.length === 0 ? (
          <EmptyState
            description="后端未返回当前项目的机会。"
            title="暂无机会"
          />
        ) : (
          <OpportunityBoard opportunities={response.items} projectId={projectId} />
        )}
      </section>
    );
  } catch (error) {
    return <ErrorState error={error} title="无法加载机会" />;
  }
}

function getSingleSearchParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) {
    return value[0] ?? null;
  }

  return value ?? null;
}
