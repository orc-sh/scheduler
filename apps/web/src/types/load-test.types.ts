/**
 * Type definitions for load test-related API responses
 */

export interface LoadTestConfiguration {
  id: string;
  project_id: string;
  webhook_id: string;
  name: string;
  concurrent_users: number;
  duration_seconds: number;
  requests_per_second?: number;
  created_at: string;
  updated_at: string;
  webhook?: {
    id: string;
    url: string;
    method: string;
    headers?: Record<string, string>;
    query_params?: Record<string, string>;
    body_template?: string;
    content_type?: string;
  };
}

export interface LoadTestRun {
  id: string;
  load_test_configuration_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface LoadTestReport {
  id: string;
  load_test_run_id: string;
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

export interface LoadTestResult {
  id: string;
  load_test_report_id: string;
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

export interface LoadTestConfigurationWithRuns extends LoadTestConfiguration {
  runs: LoadTestRun[];
}

export interface LoadTestRunWithReports extends LoadTestRun {
  reports: LoadTestReportWithResults[];
}

export interface LoadTestReportWithResults extends LoadTestReport {
  results: LoadTestResult[];
}

export interface CreateLoadTestConfigurationRequest {
  project_id?: string;
  name: string;
  url: string;
  method: string;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body_template?: string;
  content_type?: string;
  concurrent_users: number;
  duration_seconds: number;
  requests_per_second?: number;
}

export interface UpdateLoadTestConfigurationRequest {
  name?: string;
  concurrent_users?: number;
  duration_seconds?: number;
  requests_per_second?: number;
}

export interface PaginatedLoadTestConfigurationResponse {
  data: LoadTestConfiguration[];
  pagination: {
    current_page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_previous: boolean;
  };
}
