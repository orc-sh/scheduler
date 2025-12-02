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

export interface Account {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
}

export interface Job {
  id: string;
  account_id: string;
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
  account: Account;
  job: Job;
  webhook: Webhook;
}

export type JobExecutionStatus =
  | 'queued'
  | 'running'
  | 'success'
  | 'failure'
  | 'timed_out'
  | 'dead_letter';

export interface JobExecution {
  id: string;
  job_id: string;
  status: JobExecutionStatus;
  started_at: string | null;
  finished_at: string | null;
  response_code: number | null;
  response_body: string | null;
  worker_id: string | null;
  duration_ms: number | null;
  error: string | null;
  attempt: number;
  created_at: string;
}
