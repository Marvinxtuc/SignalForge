import { API_BASE_URL, API_REQUEST_TIMEOUT_MS } from "./constants";
import type {
  ApiErrorEnvelope,
  CollectionCreateRequest,
  CollectionJob,
  CollectionJobCreateResponse,
  CollectionLog,
  CredentialStatusResponse,
  CsvReportResponse,
  MarkdownReportResponse,
  Opportunity,
  PaginatedResponse,
  PaginationParams,
  PlatformsResponse,
  ProcessingRequest,
  ProcessingResponse,
  ProcessingSummary,
  Project,
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
  const url = new URL(normalizedPath, `${API_BASE_URL}/`);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
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
  projects: {
    list: (params: PaginationParams = {}) =>
      apiRequest<PaginatedResponse<Project>>("/api/projects", { query: params }),
    get: (projectId: UUID) => apiRequest<Project>(`/api/projects/${projectId}`)
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
      apiRequest<CredentialStatusResponse>("/api/settings/credentials/status")
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
  }
};
