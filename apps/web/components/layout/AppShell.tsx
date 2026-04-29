"use client";

import type { ReactNode } from "react";
import { Suspense, useEffect, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import { DEFAULT_PROJECT_NAME } from "../../lib/constants";
import type { Project } from "../../lib/types";
import { Navigation } from "./Navigation";
import { ProjectSelector } from "./ProjectSelector";

type ProjectSelectorState = {
  projects: Project[];
  selectedProjectId: string | null;
  selectedProjectName: string | null;
  matchedDefaultProject: boolean;
  errorMessage: string | null;
};

const INITIAL_PROJECT_STATE: ProjectSelectorState = {
  projects: [],
  selectedProjectId: null,
  selectedProjectName: null,
  matchedDefaultProject: false,
  errorMessage: null
};

export function AppShell({ children }: { children: ReactNode }) {
  const [projectState, setProjectState] = useState<ProjectSelectorState>(INITIAL_PROJECT_STATE);

  useEffect(() => {
    let active = true;
    getProjectSelectorState()
      .then((nextState) => {
        if (active) {
          setProjectState(nextState);
        }
      })
      .catch(() => {
        if (active) {
          setProjectState({
            ...INITIAL_PROJECT_STATE,
            errorMessage: "无法从 SignalForge 后端加载项目。"
          });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="appShell">
      <header className="topBar">
        <div className="brandLockup" aria-label="SignalForge">
          <p className="brandName">信号洞察雷达</p>
          <span className="brandPhase">前端 MVP</span>
        </div>
        <div className="statusStrip" aria-label="后端目标">
          <span className="statusDot" aria-hidden="true" />
          后端 API 已就绪
        </div>
      </header>
      <aside className="sidebar" aria-label="工作区导航">
        <div className="brandPanel" aria-label="SignalForge">
          <span className="brandMark" aria-hidden="true">
            SF
          </span>
          <div>
            <p className="brandTitle">SignalForge</p>
            <p className="brandSubtitle">研究工作台</p>
          </div>
        </div>
        <button className="sidebarAction" disabled type="button">
          新建分析
        </button>
        <Suspense fallback={null}>
          <ProjectSelector
            errorMessage={projectState.errorMessage}
            matchedDefaultProject={projectState.matchedDefaultProject}
            projects={projectState.projects}
            selectedProjectId={projectState.selectedProjectId}
            selectedProjectName={projectState.selectedProjectName}
          />
        </Suspense>
        <Suspense fallback={null}>
          <Navigation selectedProjectId={projectState.selectedProjectId} />
        </Suspense>
      </aside>
      <main className="workspaceArea">
        <div className="contentFrame">{children}</div>
      </main>
    </div>
  );
}

async function getProjectSelectorState(): Promise<ProjectSelectorState> {
  try {
    const response = await api.projects.list({ page_size: 100 });
    const projects = response.items;
    const selected =
      projects.find((project) => project.name === DEFAULT_PROJECT_NAME) ?? projects[0] ?? null;

    return {
      projects,
      selectedProjectId: selected?.id ?? null,
      selectedProjectName: selected?.name ?? null,
      matchedDefaultProject: selected?.name === DEFAULT_PROJECT_NAME,
      errorMessage: null
    };
  } catch (error) {
    return {
      projects: [],
      selectedProjectId: null,
      selectedProjectName: null,
      matchedDefaultProject: false,
      errorMessage:
        error instanceof ApiClientError
          ? `${error.code}: ${error.message}`
          : "无法从 SignalForge 后端加载项目。"
    };
  }
}
