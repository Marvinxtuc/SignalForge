export type UUID = string;
export type ISODateTime = string;

export type ApiErrorEnvelope = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
};

export type PaginationParams = {
  page?: number;
  page_size?: number;
};

export type Project = {
  id: UUID;
  name: string;
  description: string | null;
  platforms_enabled: Record<string, boolean> | null;
  collection_frequency: string;
  created_at: ISODateTime | null;
  updated_at: ISODateTime | null;
};

export type ProjectCreateRequest = {
  name: string;
  description?: string | null;
  platforms_enabled?: Record<string, boolean> | null;
  collection_frequency?: string;
};

export type KeywordType = "main" | "related" | "exclude";

export type Keyword = {
  id: UUID;
  project_id: UUID;
  keyword: string;
  keyword_type: KeywordType;
  language: string;
  enabled: boolean;
  created_at: ISODateTime | null;
  updated_at: ISODateTime | null;
};

export type KeywordCreateRequest = {
  keyword: string;
  keyword_type: KeywordType;
  language?: string;
  enabled?: boolean;
};

export type SignalStatus = "new" | "saved" | "ignored" | "reviewed";
export type SignalFeedback = "valuable" | "not_valuable" | "wrong_type" | "ignored";

export type Signal = {
  id: UUID;
  raw_item_id: UUID;
  project_id: UUID;
  is_need_signal: boolean;
  signal_type: string | null;
  pain_level: number | null;
  clarity_score: number | null;
  urgency_score: number | null;
  business_relevance: number | null;
  model_confidence: number | null;
  signal_confidence: number | null;
  summary_zh: string | null;
  recommended_action: string | null;
  user_feedback: string | null;
  status: string;
  created_at: ISODateTime;
  updated_at: ISODateTime;
  platform: string;
  source_url: string;
  content_excerpt: string | null;
  keyword_hits: string[] | null;
  engagement: Record<string, unknown> | null;
  created_at_source: ISODateTime | null;
};

export type SignalListParams = PaginationParams & {
  platform?: string;
  signal_type?: string;
  min_pain_level?: number;
  keyword?: string;
  status?: string;
  date_from?: ISODateTime;
  date_to?: ISODateTime;
};

export type OpportunityStatus =
  | "new"
  | "watching"
  | "validating"
  | "build_candidate"
  | "content_candidate"
  | "archived";

export type Opportunity = {
  id: UUID;
  project_id: UUID;
  cluster_id: UUID | null;
  title: string;
  description: string | null;
  status: string;
  opportunity_score: number | null;
  evidence_count: number;
  platform_distribution: Record<string, unknown> | null;
  last_seen_at: ISODateTime | null;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

export type CollectionLog = {
  id: UUID;
  job_id: UUID;
  platform: string;
  status: string;
  items_collected: number;
  items_inserted: number;
  items_skipped: number;
  error_message: string | null;
  rate_limit_remaining: number | null;
  rate_limit_reset_at: ISODateTime | null;
  created_at: ISODateTime;
};

export type CollectionJob = {
  id: UUID;
  project_id: UUID;
  status: string;
  trigger_type: string;
  started_at: ISODateTime | null;
  finished_at: ISODateTime | null;
  error_summary: string | null;
  created_at: ISODateTime;
};

export type CollectionJobCreateResponse = CollectionJob & {
  collector_execution: string;
  log: CollectionLog | null;
};

export type CollectionCreateRequest = {
  execution_mode?: string;
};

export type PlatformName = "reddit" | "product_hunt" | "x" | "discord";
export type PlatformPhase = "P0" | "P1" | "P2";
export type CredentialStatus =
  | "available"
  | "missing"
  | "missing_env"
  | "configured"
  | "configured_unverified"
  | "valid"
  | "invalid"
  | "permission_limited"
  | "rate_limited"
  | "disabled"
  | "coming_soon";

export type PlatformStatus = {
  platform: PlatformName;
  phase: PlatformPhase;
  enabled_for_mvp: boolean;
  status: CredentialStatus;
};

export type PlatformsResponse = {
  platforms: PlatformStatus[];
};

export type CredentialStatusItem = {
  platform: PlatformName;
  status: CredentialStatus;
  credential_name: string | null;
  last_checked_at: ISODateTime | null;
};

export type CredentialStatusResponse = {
  credentials: CredentialStatusItem[];
};

export type PlatformEnvTestResponse = {
  platform: string;
  status: CredentialStatus;
  message: string;
  checked_at: ISODateTime;
  required_env_missing: string[];
};

export type ReportRequest = {
  days?: number;
  min_pain_level?: number;
  top_clusters_limit?: number;
  opportunities_limit?: number;
};

export type MarkdownReportResponse = {
  format: "markdown" | string;
  content: string;
  generated_at: ISODateTime;
};

export type CsvReportResponse = {
  format: "csv" | string;
  filename: string;
  content_type: string;
  content: string;
  generated_at: ISODateTime;
};

export type ProcessingRequest = {
  mode?: "mock" | "fallback_only" | string;
  reprocess?: boolean;
};

export type ProcessingTopSignal = {
  signal_id: string;
  raw_item_id: string;
  platform: string;
  source_url: string;
  signal_type: string | null;
  pain_level: number | null;
  signal_confidence: number | null;
  summary_zh: string | null;
};

export type ProcessingSummary = {
  total_raw_items: number;
  processed_raw_items: number;
  total_signals: number;
  high_value_signals: number;
  high_value_ratio: number;
  noise_ratio: number;
  llm_json_failure_count: number;
  fallback_classification_count: number;
  cluster_coverage_rate: number;
  opportunity_count: number;
  embedding_count: number;
  cluster_count: number;
  top_5_high_value_signals: ProcessingTopSignal[];
};

export type ProcessingResponse = ProcessingSummary & {
  project_id: UUID;
  mode: string;
  reprocess: boolean;
  processed_in_run: number;
  skipped_existing: number;
  skipped_deleted: number;
  status: string;
  details: Record<string, unknown>;
};

export type ProductionRunMode = "mock" | "preview" | "production";

export type ProductionRunApprovals = {
  real_platform_read: boolean;
  real_platform_write: boolean;
  real_llm: boolean;
  real_embedding: boolean;
  confirmation_text: string;
};

export type ProductionRunCreateRequest = {
  mode: ProductionRunMode;
  collection_execution_mode: string;
  processing_mode: string;
  reprocess: boolean;
  approvals: ProductionRunApprovals;
};

export type ProductionRunRead = {
  id: UUID;
  project_id: UUID | null;
  status: string;
  stage: string;
  collection_mode: string;
  processing_mode: string;
  allow_real_platform_write: boolean;
  allow_real_llm: boolean;
  allow_real_embedding: boolean;
  env_preflight: Record<string, unknown>;
  result_summary: Record<string, unknown>;
  error_summary: string | null;
  rollback_hint: string | null;
  redacted_logs: Array<Record<string, unknown>>;
  started_at: ISODateTime | null;
  finished_at: ISODateTime | null;
  created_at: ISODateTime | null;
  updated_at: ISODateTime | null;
};

export type ProductionRunStatus = {
  project_id: UUID;
  checked_at: ISODateTime;
  collection_logs: CollectionLog[];
  processing_summary: ProcessingSummary;
};

export type ProductionRunListItem = {
  id: UUID;
  project_id: UUID;
  created_at: ISODateTime;
  state: "collect" | "process" | "review" | "report" | "closeout";
  status: string;
  mode: ProductionRunMode | string;
  collection_job_id: UUID | null;
  processing_mode: string | null;
  items_inserted: number | null;
  total_signals: number | null;
  error_message: string | null;
};
