"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, ApiClientError } from "../../lib/api";
import { ROUTES } from "../../lib/constants";
import type { KeywordType } from "../../lib/types";
import { Button } from "../../components/ui/Button";

type SubmitState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string };

export default function OnboardingPage() {
  const router = useRouter();
  const [projectName, setProjectName] = useState("Personal Production E2E");
  const [includeKeywords, setIncludeKeywords] = useState("wallet onboarding, pricing clarity");
  const [excludeKeywords, setExcludeKeywords] = useState("giveaway");
  const [mockEnabled, setMockEnabled] = useState(true);
  const [state, setState] = useState<SubmitState>({ status: "idle" });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState({ status: "loading" });

    try {
      const project = await api.projects.create({
        name: projectName.trim(),
        description: "Created by Personal Production v1 onboarding.",
        platforms_enabled: { mock: mockEnabled },
        collection_frequency: "manual"
      });

      const includeItems = parseKeywords(includeKeywords);
      const excludeItems = parseKeywords(excludeKeywords);
      await Promise.all([
        ...includeItems.map((keyword, index) =>
          createKeyword(project.id, keyword, index === 0 ? "main" : "related")
        ),
        ...excludeItems.map((keyword) => createKeyword(project.id, keyword, "exclude"))
      ]);

      router.push(`${ROUTES.dashboard}?${new URLSearchParams({ projectId: project.id })}`);
    } catch (error) {
      setState({ status: "error", message: formatActionError(error) });
    }
  }

  const isSubmitting = state.status === "loading";

  return (
    <section className="detailPage">
      <header className="pageHeader">
        <div>
          <p className="pageEyebrow">Onboarding</p>
          <h1 className="pageTitle">创建个人信号项目</h1>
          <p className="pageSubtitle">
            创建项目、关键词和 mock 平台配置，然后进入业务闭环控制台。
          </p>
        </div>
      </header>

      <form className="surfacePanel" onSubmit={(event) => void handleSubmit(event)}>
        <div className="reportOptionsGrid">
          <label className="compactField">
            <span>项目名称</span>
            <input
              className="selectControl"
              disabled={isSubmitting}
              minLength={1}
              onChange={(event) => setProjectName(event.target.value)}
              required
              type="text"
              value={projectName}
            />
          </label>
          <label className="compactField">
            <span>Include keywords</span>
            <input
              className="selectControl"
              disabled={isSubmitting}
              onChange={(event) => setIncludeKeywords(event.target.value)}
              required
              type="text"
              value={includeKeywords}
            />
          </label>
          <label className="compactField">
            <span>Exclude keywords</span>
            <input
              className="selectControl"
              disabled={isSubmitting}
              onChange={(event) => setExcludeKeywords(event.target.value)}
              type="text"
              value={excludeKeywords}
            />
          </label>
          <label className="compactField">
            <span>平台</span>
            <select
              className="selectControl"
              disabled={isSubmitting}
              onChange={(event) => setMockEnabled(event.target.value === "mock")}
              value={mockEnabled ? "mock" : ""}
            >
              <option value="mock">mock</option>
            </select>
          </label>
        </div>

        <div className="detailActions">
          <label className="compactField">
            <span>
              <input
                checked={mockEnabled}
                disabled={isSubmitting}
                onChange={(event) => setMockEnabled(event.target.checked)}
                type="checkbox"
              />{" "}
              mock 平台
            </span>
          </label>
          <Button disabled={isSubmitting || !projectName.trim()} type="submit" variant="primary">
            {isSubmitting ? "创建中" : "创建项目并进入 Dashboard"}
          </Button>
        </div>

        {state.status === "error" ? (
          <p className="inlineError" role="alert">
            {state.message}
          </p>
        ) : null}
      </form>
    </section>
  );
}

function parseKeywords(value: string): string[] {
  return value
    .split(",")
    .map((keyword) => keyword.trim())
    .filter(Boolean);
}

function createKeyword(projectId: string, keyword: string, keywordType: KeywordType) {
  return api.keywords.create(projectId, {
    keyword,
    keyword_type: keywordType,
    language: "all",
    enabled: true
  });
}

function formatActionError(error: unknown): string {
  if (error instanceof ApiClientError) {
    return `${error.code}${error.status ? ` (${error.status})` : ""}: ${error.message}`;
  }

  return "未知前端错误。";
}
