"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { Suspense, useEffect, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import { DEFAULT_PROJECT_NAME, ROUTES } from "../../lib/constants";
import type { Project } from "../../lib/types";
import { Navigation } from "./Navigation";
import { ProjectSelector } from "./ProjectSelector";

type ProjectSelectorState = {
  backendStatus: "connected" | "partial" | "unavailable";
  backendStatusLabel: string;
  projects: Project[];
  selectedProjectId: string | null;
  selectedProjectName: string | null;
  matchedDefaultProject: boolean;
  errorMessage: string | null;
};

const INITIAL_PROJECT_STATE: ProjectSelectorState = {
  backendStatus: "unavailable",
  backendStatusLabel: "后端不可用",
  projects: [],
  selectedProjectId: null,
  selectedProjectName: null,
  matchedDefaultProject: false,
  errorMessage: null
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [projectState, setProjectState] = useState<ProjectSelectorState>(INITIAL_PROJECT_STATE);

  useEffect(() => {
    if (pathname === "/login") {
      return;
    }

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
            backendStatus: "unavailable",
            backendStatusLabel: "后端不可用",
            errorMessage: "无法从 SignalForge 后端加载项目。"
          });
        }
      });

    return () => {
      active = false;
    };
  }, [pathname]);

  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="appShell">
      <header className="topBar">
        <div className="brandLockup" aria-label="SignalForge">
          <p className="brandName">信号洞察雷达</p>
          <span className="brandPhase">前端 MVP</span>
        </div>
        <div className="statusStrip" aria-label="后端状态">
          <span
            className="statusDot"
            style={{ background: BACKEND_STATUS_COLOR[projectState.backendStatus] }}
            aria-hidden="true"
          />
          {projectState.backendStatusLabel}
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
        <Link className="sidebarAction" href={`${ROUTES.onboarding}?new=1`}>
          新建分析
        </Link>
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
  const [healthResult, projectsResult] = await Promise.allSettled([
    api.health(),
    api.projects.list({ page_size: 100 })
  ]);
  const healthOk = healthResult.status === "fulfilled";
  const projectsOk = projectsResult.status === "fulfilled";
  const backendStatus = getBackendStatus(healthOk, projectsOk);

  if (projectsOk) {
    const projects = projectsResult.value.items;
    const selected =
      projects.find((project) => project.name === DEFAULT_PROJECT_NAME) ?? projects[0] ?? null;

    return {
      backendStatus,
      backendStatusLabel: BACKEND_STATUS_LABEL[backendStatus],
      projects,
      selectedProjectId: selected?.id ?? null,
      selectedProjectName: selected?.name ?? null,
      matchedDefaultProject: selected?.name === DEFAULT_PROJECT_NAME,
      errorMessage: null
    };
  }

  const projectsError = projectsResult.reason;

  return {
    backendStatus,
    backendStatusLabel: BACKEND_STATUS_LABEL[backendStatus],
    projects: [],
    selectedProjectId: null,
    selectedProjectName: null,
    matchedDefaultProject: false,
    errorMessage:
      projectsError instanceof ApiClientError
        ? `${projectsError.code}: ${projectsError.message}`
        : "无法从 SignalForge 后端加载项目。"
  };
}

const BACKEND_STATUS_LABEL: Record<ProjectSelectorState["backendStatus"], string> = {
  connected: "后端已连接",
  partial: "后端部分可用",
  unavailable: "后端不可用"
};

const BACKEND_STATUS_COLOR: Record<ProjectSelectorState["backendStatus"], string> = {
  connected: "var(--positive)",
  partial: "#f59e0b",
  unavailable: "#ef4444"
};

function getBackendStatus(
  healthOk: boolean,
  projectsOk: boolean
): ProjectSelectorState["backendStatus"] {
  if (healthOk && projectsOk) {
    return "connected";
  }

  if (healthOk || projectsOk) {
    return "partial";
  }

  return "unavailable";
}
