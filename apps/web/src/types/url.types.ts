/**
 * Type definitions for URL-related API responses
 */

export interface Url {
  id: string;
  project_id: string;
  unique_identifier: string;
  path: string;
  created_at: string;
  updated_at: string;
  project?: {
    id: string;
    user_id: string;
    name: string;
    created_at: string;
  };
}

export interface UrlLog {
  id: string;
  url_id: string;
  method: string;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body?: string;
  response_status?: number;
  response_headers?: Record<string, string>;
  response_body?: string;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface UrlWithLogs extends Url {
  logs: UrlLog[];
}

export interface CreateUrlRequest {
  project_id: string;
}

export interface PaginatedUrlResponse {
  data: Url[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_entries: number;
    page_size: number;
    has_next: boolean;
    has_previous: boolean;
    next_page: number | null;
    previous_page: number | null;
  };
}
