"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Opportunity, PaginatedResponse } from "../../lib/types";
import { EmptyState } from "../ui/EmptyState";
import { ErrorState } from "../ui/ErrorState";
import { LoadingState } from "../ui/LoadingState";
import { OpportunityBoard } from "./OpportunityBoard";

type OpportunitiesState =
  | { status: "idle" | "loading" }
  | { status: "ready"; response: PaginatedResponse<Opportunity> }
  | { status: "error"; error: unknown };

export function OpportunitiesPage() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId");
  const [state, setState] = useState<OpportunitiesState>({ status: "idle" });

  useEffect(() => {
    if (!projectId) {
      setState({ status: "idle" });
      return;
    }

    let active = true;
    setState({ status: "loading" });

    api.opportunities
      .list(projectId, { page_size: 100 })
      .then((response) => {
        if (active) {
          setState({ status: "ready", response });
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({ status: "error", error });
        }
      });

    return () => {
      active = false;
    };
  }, [projectId]);

  if (!projectId) {
    return (
      <EmptyState
        description="请先在侧边栏选择项目，以加载项目机会。"
        title="请选择项目"
      />
    );
  }

  if (state.status === "idle" || state.status === "loading") {
    return <LoadingState label="正在加载机会" />;
  }

  if (state.status === "error") {
    return <ErrorState error={state.error} title="无法加载机会" />;
  }

  if (state.status !== "ready") {
    return null;
  }

  const response = state.response;

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
}
