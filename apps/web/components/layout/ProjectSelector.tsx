"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { DEFAULT_PROJECT_NAME, ROUTES } from "../../lib/constants";
import type { Project } from "../../lib/types";

type ProjectSelectorProps = {
  projects: Project[];
  selectedProjectId: string | null;
  selectedProjectName: string | null;
  matchedDefaultProject: boolean;
  errorMessage: string | null;
};

export function ProjectSelector({
  errorMessage,
  matchedDefaultProject,
  projects,
  selectedProjectId,
  selectedProjectName
}: ProjectSelectorProps) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryProjectId = searchParams.get("projectId");
  const projectIds = new Set(projects.map((project) => project.id));
  const activeProjectId =
    queryProjectId && projectIds.has(queryProjectId) ? queryProjectId : selectedProjectId ?? "";

  useEffect(() => {
    if (queryProjectId || !selectedProjectId) {
      return;
    }

    const params = new URLSearchParams(searchParams.toString());
    params.set("projectId", selectedProjectId);
    router.replace(`${pathname || ROUTES.signals}?${params.toString()}`);
  }, [pathname, queryProjectId, router, searchParams, selectedProjectId]);

  function handleProjectChange(nextProjectId: string) {
    if (!nextProjectId) {
      return;
    }

    const params = new URLSearchParams(searchParams.toString());
    params.set("projectId", nextProjectId);
    router.push(`${pathname || ROUTES.signals}?${params.toString()}`);
  }

  return (
    <section className="projectSelector" aria-labelledby="project-selector-label">
      <p className="sectionLabel" id="project-selector-label">
        项目
      </p>
      <select
        aria-label="项目选择器"
        className="selectControl"
        disabled={projects.length === 0}
        onChange={(event) => handleProjectChange(event.target.value)}
        value={activeProjectId}
      >
        {projects.length === 0 ? (
          <option value="">暂无可用项目</option>
        ) : (
          projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))
        )}
      </select>
      <p className="selectorMeta">
        {errorMessage
          ? errorMessage
          : projects.length === 0
            ? "后端未返回项目，选择器已禁用。"
            : activeProjectId === selectedProjectId
              ? matchedDefaultProject
                ? `默认项目：${DEFAULT_PROJECT_NAME}`
                : `默认项目：${selectedProjectName ?? "第一个现有项目"}`
              : "仅可选择已有后端项目。"}
      </p>
    </section>
  );
}
