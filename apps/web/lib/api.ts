import {
  API_REQUEST_TIMEOUT_MS,
  HAS_PUBLIC_API_BASE_URL_OVERRIDE,
  PUBLIC_API_BASE_URL,
  SERVER_API_BASE_URL
} from "./constants";
import type {
  ApiErrorEnvelope,
  CollectionCreateRequest,
  CollectionJob,
  CollectionJobCreateResponse,
  CollectionLog,
  CredentialStatusResponse,
  CsvReportResponse,
  Keyword,
  KeywordCreateRequest,
  MarkdownReportResponse,
  Opportunity,
  OpportunityStatus,
  PaginatedResponse,
  PaginationParams,
  PlatformsResponse,
  PlatformEnvTestResponse,
  ProcessingRequest,
  ProcessingResponse,
  ProcessingSummary,
  ProductionRunCreateRequest,
  ProductionRunListItem,
  ProductionRunRead,
  ProductionRunStatus,
  Project,
  ProjectCreateRequest,
  ReportRequest,
  Signal,
  SignalFeedback,
  SignalListParams,
  SignalStatus,
  UUID
} from "./types";

type QueryValue = string | number | boolean | null | undefined;
type QueryParams = Record<string, QueryValue>;

type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  query?: QueryParams;
  timeoutMs?: number;
};

export type HealthResponse = Record<string, unknown>;

export class ApiClientError extends Error {
  readonly status: number | null;
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly url: string;

  constructor(input: {
    message: string;
    code: string;
    url: string;
    status?: number | null;
    details?: Record<string, unknown>;
  }) {
    super(input.message);
    this.name = "ApiClientError";
    this.code = input.code;
    this.status = input.status ?? null;
    this.details = input.details ?? {};
    this.url = input.url;
  }
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, query, timeoutMs, ...requestInit } = options;
  const url = buildBackendUrl(path, query);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs ?? API_REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...requestInit,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: requestInit.cache ?? "no-store",
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...getServerOwnerAuthHeader(),
        ...requestInit.headers
      },
      signal: requestInit.signal ?? controller.signal
    });

    return await parseApiResponse<T>(response, url);
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }

    const aborted = error instanceof DOMException && error.name === "AbortError";
    throw new ApiClientError({
      code: aborted ? "network_timeout" : "network_error",
      message: aborted
        ? "SignalForge backend request timed out."
        : "SignalForge backend is unreachable.",
      url
    });
  } finally {
    clearTimeout(timeout);
  }
}

function buildBackendUrl(path: string, query?: QueryParams): string {
  if (/^https?:\/\//i.test(path)) {
    throw new ApiClientError({
      code: "invalid_backend_path",
      message: "API client only accepts SignalForge backend-relative paths.",
      url: path
    });
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const resolvedUrl = resolveApiUrl(normalizedPath);
  const url = new URL(resolvedUrl, "http://signalforge.local");

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return isAbsoluteUrl(resolvedUrl) ? url.toString() : `${url.pathname}${url.search}`;
}

function resolveApiUrl(path: string): string {
  if (typeof window === "undefined") {
    return new URL(path, `${SERVER_API_BASE_URL}/`).toString();
  }

  assertAllowedPublicApiBase();

  if (!HAS_PUBLIC_API_BASE_URL_OVERRIDE || PUBLIC_API_BASE_URL === "/api") {
    return toBrowserProxyPath(path);
  }

  if (isAbsoluteUrl(PUBLIC_API_BASE_URL)) {
    return new URL(path, `${PUBLIC_API_BASE_URL}/`).toString();
  }

  return joinRelativePath(PUBLIC_API_BASE_URL, path);
}

function toBrowserProxyPath(path: string): string {
  if (path === "/health") {
    return "/api/health";
  }

  if (path === "/api" || path.startsWith("/api/")) {
    return path;
  }

  return `/api${path}`;
}

function joinRelativePath(base: string, path: string): string {
  const normalizedBase = base.startsWith("/") ? base : `/${base}`;
  const normalizedPath =
    normalizedBase.endsWith("/api") && path.startsWith("/api/")
      ? path.slice("/api".length)
      : path;

  return `${normalizedBase.replace(/\/+$/, "")}/${normalizedPath.replace(/^\/+/, "")}`;
}

function assertAllowedPublicApiBase(): void {
  if (
    process.env.NODE_ENV !== "production" ||
    !isLocalhostBase(PUBLIC_API_BASE_URL) ||
    isLocalhost(window.location.hostname)
  ) {
    return;
  }

  throw new ApiClientError({
    code: "invalid_public_api_base",
    message: "Production browser API base cannot point to localhost from an external host.",
    url: PUBLIC_API_BASE_URL
  });
}

function isLocalhostBase(baseUrl: string): boolean {
  if (!isAbsoluteUrl(baseUrl)) {
    return false;
  }

  return isLocalhost(new URL(baseUrl).hostname);
}

function isAbsoluteUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

function isLocalhost(hostname: string): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

function getServerOwnerAuthHeader(): Record<string, string> {
  if (typeof window !== "undefined") {
    return {};
  }

  const authRequired = ["1", "true", "yes", "on"].includes(
    (process.env.SIGNALFORGE_REQUIRE_OWNER_AUTH ?? "").trim().toLowerCase()
  );
  const ownerToken = process.env.SIGNALFORGE_OWNER_API_TOKEN?.trim();

  if (!authRequired || !ownerToken) {
    return {};
  }

  return { "X-SignalForge-Owner-Token": ownerToken };
}

async function parseApiResponse<T>(response: Response, url: string): Promise<T> {
  const text = await response.text();
  const payload = text ? parseJson(text, url, response.status) : null;

  if (!response.ok) {
    const backendError = extractBackendError(payload);
    throw new ApiClientError({
      code: backendError?.code ?? statusCodeToErrorCode(response.status),
      message: backendError?.message ?? statusCodeToMessage(response.status),
      status: response.status,
      details: backendError?.details,
      url
    });
  }

  return payload as T;
}

function parseJson(text: string, url: string, status: number): unknown {
  try {
    return JSON.parse(text);
  } catch {
    throw new ApiClientError({
      code: "invalid_response",
      message: "SignalForge backend returned a non-JSON response.",
      status,
      url
    });
  }
}

function extractBackendError(payload: unknown): ApiErrorEnvelope["error"] | null {
  if (!payload || typeof payload !== "object" || !("error" in payload)) {
    return null;
  }

  const error = (payload as ApiErrorEnvelope).error;
  if (!error || typeof error.code !== "string" || typeof error.message !== "string") {
    return null;
  }

  return {
    code: error.code,
    message: error.message,
    details:
      error.details && typeof error.details === "object" && !Array.isArray(error.details)
        ? error.details
        : {}
  };
}

function statusCodeToErrorCode(status: number): string {
  if (status === 404) {
    return "not_found";
  }

  if (status >= 500) {
    return "server_error";
  }

  return "http_error";
}

function statusCodeToMessage(status: number): string {
  if (status === 404) {
    return "Requested SignalForge resource was not found.";
  }

  if (status >= 500) {
    return "SignalForge backend returned a server error.";
  }

  return `SignalForge backend request failed with status ${status}.`;
}

export const api = {
  health: () => apiRequest<HealthResponse>("/health"),
  projects: {
    list: (params: PaginationParams = {}) =>
      apiRequest<PaginatedResponse<Project>>("/api/projects", { query: params }),
    get: (projectId: UUID) => apiRequest<Project>(`/api/projects/${projectId}`),
    create: (body: ProjectCreateRequest) =>
      apiRequest<Project>("/api/projects", {
        method: "POST",
        body
      })
  },
  keywords: {
    list: (projectId: UUID) => apiRequest<Keyword[]>(`/api/projects/${projectId}/keywords`),
    create: (projectId: UUID, body: KeywordCreateRequest) =>
      apiRequest<Keyword>(`/api/projects/${projectId}/keywords`, {
        method: "POST",
        body
      })
  },
  signals: {
    list: (projectId: UUID, params: SignalListParams = {}) =>
      apiRequest<PaginatedResponse<Signal>>(`/api/projects/${projectId}/signals`, {
        query: params
      }),
    get: (signalId: UUID) => apiRequest<Signal>(`/api/signals/${signalId}`),
    updateFeedback: (signalId: UUID, user_feedback: SignalFeedback) =>
      apiRequest<Signal>(`/api/signals/${signalId}/feedback`, {
        method: "PUT",
        body: { user_feedback }
      }),
    updateStatus: (signalId: UUID, status: SignalStatus) =>
      apiRequest<Signal>(`/api/signals/${signalId}/status`, {
        method: "PUT",
        body: { status }
      })
  },
  opportunities: {
    list: (projectId: UUID, params: PaginationParams = {}) =>
      apiRequest<PaginatedResponse<Opportunity>>(`/api/projects/${projectId}/opportunities`, {
        query: params
      }),
    get: (opportunityId: UUID) => apiRequest<Opportunity>(`/api/opportunities/${opportunityId}`),
    createFromSignal: (signalId: UUID) =>
      apiRequest<Opportunity>(`/api/signals/${signalId}/create-opportunity`, {
        method: "POST"
      }),
    updateStatus: (opportunityId: UUID, status: OpportunityStatus) =>
      apiRequest<Opportunity>(`/api/opportunities/${opportunityId}`, {
        method: "PUT",
        body: { status }
      }),
    archive: (opportunityId: UUID) =>
      apiRequest<Opportunity>(`/api/opportunities/${opportunityId}/archive`, {
        method: "POST"
      })
  },
  collection: {
    collect: (projectId: UUID, body: CollectionCreateRequest = {}) =>
      apiRequest<CollectionJobCreateResponse>(`/api/projects/${projectId}/collect`, {
        method: "POST",
        body
      }),
    getJob: (jobId: UUID) => apiRequest<CollectionJob>(`/api/jobs/${jobId}`),
    listLogs: (projectId: UUID, params: PaginationParams = {}) =>
      apiRequest<PaginatedResponse<CollectionLog>>(
        `/api/projects/${projectId}/collection-logs`,
        { query: params }
      )
  },
  settings: {
    platforms: () => apiRequest<PlatformsResponse>("/api/settings/platforms"),
    credentialStatus: () =>
      apiRequest<CredentialStatusResponse>("/api/settings/credentials/status"),
    testPlatform: (platform: string) =>
      apiRequest<PlatformEnvTestResponse>(`/api/settings/platforms/${platform}/test`, {
        method: "POST"
      })
  },
  reports: {
    markdown: (projectId: UUID, body: ReportRequest = {}) =>
      apiRequest<MarkdownReportResponse>(`/api/projects/${projectId}/reports/markdown`, {
        method: "POST",
        body
      }),
    csv: (projectId: UUID, body: ReportRequest = {}) =>
      apiRequest<CsvReportResponse>(`/api/projects/${projectId}/reports/csv`, {
        method: "POST",
        body
      })
  },
  processing: {
    run: (projectId: UUID, body: ProcessingRequest = {}) =>
      apiRequest<ProcessingResponse>(`/api/projects/${projectId}/process`, {
        method: "POST",
        body
      }),
    summary: (projectId: UUID) =>
      apiRequest<ProcessingSummary>(`/api/projects/${projectId}/processing-summary`)
  },
  production: {
    createRun: (projectId: UUID, body: ProductionRunCreateRequest) =>
      apiRequest<ProductionRunRead>("/api/production/runs", {
        method: "POST",
        body: {
          project_id: projectId,
          collection_mode: body.collection_execution_mode,
          processing_mode: body.processing_mode,
          allow_real_platform_write: body.approvals.real_platform_write,
          allow_real_llm: body.approvals.real_llm,
          allow_real_embedding: body.approvals.real_embedding,
          reprocess: body.reprocess,
          execute: true,
          rollback_hint: `Frontend run mode=${body.mode}; reprocess=${body.reprocess}.`
        }
      }),
    getRun: (runId: UUID) => apiRequest<ProductionRunRead>(`/api/production/runs/${runId}`),
    status: async (projectId: UUID): Promise<ProductionRunStatus> => {
      const [logs, summary] = await Promise.all([
        api.collection.listLogs(projectId, { page_size: 10 }),
        api.processing.summary(projectId)
      ]);

      return {
        project_id: projectId,
        checked_at: new Date().toISOString(),
        collection_logs: logs.items,
        processing_summary: summary
      };
    },
    listRuns: async (projectId: UUID): Promise<ProductionRunListItem[]> => {
      const response = await apiRequest<PaginatedResponse<ProductionRunRead>>(
        "/api/production/runs",
        { query: { page_size: 20 } }
      );

      return response.items
        .filter((run) => run.project_id === projectId)
        .map(productionRunToListItem);
    }
  }
};

function productionRunToListItem(run: ProductionRunRead): ProductionRunListItem {
  const collectionSummary = asRecord(run.result_summary.collection);
  const processingSummary = asRecord(run.result_summary.processing);

  return {
    id: run.id,
    project_id: run.project_id ?? "",
    created_at: run.created_at ?? run.started_at ?? new Date().toISOString(),
    state: formatProductionRunStage(run.stage),
    status: run.status,
    mode: run.collection_mode,
    collection_job_id: typeof collectionSummary.job_id === "string" ? collectionSummary.job_id : null,
    processing_mode: run.processing_mode,
    items_inserted: numberValue(collectionSummary.items_inserted),
    total_signals: numberValue(processingSummary.total_signals),
    error_message: run.error_summary
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" ? value : null;
}

function formatProductionRunStage(runStage: string): ProductionRunListItem["state"] {
  if (runStage === "collect" || runStage === "process" || runStage === "review" || runStage === "report") {
    return runStage;
  }

  return runStage === "closeout" ? "closeout" : "review";
}
