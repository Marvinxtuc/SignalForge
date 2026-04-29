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
            errorMessage: "Unable to load projects from SignalForge backend."
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
          <p className="brandName">SignalForge</p>
          <span className="brandPhase">Phase 6 Frontend MVP</span>
        </div>
        <div className="statusStrip" aria-label="Backend target">
          <span className="statusDot" aria-hidden="true" />
          Backend API client ready
        </div>
      </header>
      <aside className="sidebar" aria-label="Workspace navigation">
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
          : "Unable to load projects from SignalForge backend."
    };
  }
}
