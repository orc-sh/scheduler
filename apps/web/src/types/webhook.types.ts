/**
 * Types for Webhook and Job API
 */

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface CreateJobRequest {
  name: string;
  schedule: string;
  type: number;
  timezone?: string;
  enabled?: boolean;
}

export interface CreateWebhookRequest {
  url: string;
  method?: HttpMethod;
  headers?: Record<string, string>;
  query_params?: Record<string, string>;
  body_template?: string;
  content_type?: string;
}

export interface CreateCronWebhookRequest {
  job: CreateJobRequest;
  webhook: CreateWebhookRequest;
}

export interface Project {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
}

export interface Job {
  id: string;
  project_id: string;
  name: string;
  schedule: string;
  type: number;
  timezone: string;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string;
  created_at: string;
  updated_at: string;
}

export interface Webhook {
  id: string;
  job_id: string;
  url: string;
  method: HttpMethod;
  headers: Record<string, string> | null;
  query_params: Record<string, string> | null;
  body_template: string | null;
  content_type: string;
  created_at: string;
  updated_at: string;
  job?: Job | null;
}

export interface CronWebhookResponse {
  project: Project;
  job: Job;
  webhook: Webhook;
}
