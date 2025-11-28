/**
 * Type definitions for collection-related API responses
 */

export interface Webhook {
  id: string;
  url: string;
  method: string;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body_template?: string;
  content_type?: string;
}

export interface Collection {
  id: string;
  project_id: string;
  name?: string;
  description?: string;
  created_at: string;
  updated_at: string;
  webhooks: Webhook[];
}

export interface CollectionRun {
  id: string;
  collection_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  concurrent_users: number;
  duration_seconds: number;
  requests_per_second?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  collection?: Collection;
}

export interface CollectionReport {
  id: string;
  collection_run_id: string;
  name?: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_response_time_ms?: number;
  min_response_time_ms?: number;
  max_response_time_ms?: number;
  p95_response_time_ms?: number;
  p99_response_time_ms?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CollectionResult {
  id: string;
  collection_report_id: string;
  endpoint_path: string;
  method: string;
  request_headers?: Record<string, string>;
  request_body?: string;
  response_status?: number;
  response_headers?: Record<string, string>;
  response_body?: string;
  response_time_ms: number;
  error_message?: string;
  is_success: boolean;
  created_at: string;
}

export interface CollectionWithRuns extends Collection {
  runs: CollectionRun[];
}

export interface CollectionRunWithReports extends CollectionRun {
  reports: CollectionReportWithResults[];
}

export interface CollectionReportWithResults extends CollectionReport {
  results: CollectionResult[];
}

export interface CreateCollectionRequest {
  project_id?: string;
  name?: string;
  description?: string;
}

export interface CreateWebhookRequest {
  url: string;
  method: string;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body_template?: string;
  content_type?: string;
}

export interface UpdateWebhookRequest {
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body_template?: string;
  content_type?: string;
}

export interface UpdateCollectionRequest {
  name?: string;
  description?: string;
}

export interface CreateCollectionRunRequest {
  collection_id: string;
  concurrent_users: number;
  duration_seconds: number;
  requests_per_second?: number;
}

export interface PaginatedCollectionResponse {
  data: Collection[];
  pagination: {
    current_page: number;
    page_size: number;
    total_entries: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}
