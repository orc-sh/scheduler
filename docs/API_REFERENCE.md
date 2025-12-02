# API Reference

Complete API documentation for the Scheduler service, including all endpoints, request/response formats, and usage examples.

## Table of Contents

- [Base URL](#base-url)
- [Authentication](#authentication)
- [Job Management](#job-management)
- [Webhook Management](#webhook-management)
- [Health & Metrics](#health--metrics)
- [Error Handling](#error-handling)
- [Code Examples](#code-examples)

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Set via environment variable or deployment configuration

All API endpoints are prefixed with `/api` except health and metrics endpoints.

## Authentication

All API endpoints (except health checks) require JWT authentication via Bearer token.

### Authentication Header

```
Authorization: Bearer <jwt_token>
```

### Getting a Token

Tokens are obtained through the authentication service (port 8001). See authentication service documentation for OAuth flow.

### Token Validation

The scheduler service validates JWT tokens locally using the shared `SUPABASE_JWT_SECRET`. No external auth service calls are required.

## Job Management

### Create Job

Create a new scheduled job.

**Endpoint**: `POST /api/jobs`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "account_id": "uuid",
  "name": "Daily Backup",
  "schedule": "0 2 * * *",
  "type": 1,
  "timezone": "UTC",
  "enabled": true
}
```

**Fields**:
- `account_id` (required): UUID of the account
- `name` (required): Job name (max 255 characters)
- `schedule` (required): Cron expression (e.g., "0 2 * * *" for daily at 2 AM)
- `type` (required): Job type identifier (integer)
- `timezone` (optional): Timezone for schedule (default: "UTC")
- `enabled` (optional): Whether job is enabled (default: true)

**Response**: `201 Created`
```json
{
  "id": "job-uuid",
  "account_id": "account-uuid",
  "name": "Daily Backup",
  "schedule": "0 2 * * *",
  "type": 1,
  "timezone": "UTC",
  "enabled": true,
  "last_run_at": null,
  "next_run_at": "2024-01-02T02:00:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Invalid cron expression or validation error
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User doesn't have access to account

**Example**:
```bash
curl -X POST http://localhost:8000/api/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Daily Backup",
    "schedule": "0 2 * * *",
    "type": 1
  }'
```

### Get Job

Get a specific job by ID.

**Endpoint**: `GET /api/jobs/{job_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "id": "job-uuid",
  "account_id": "account-uuid",
  "name": "Daily Backup",
  "schedule": "0 2 * * *",
  "type": 1,
  "timezone": "UTC",
  "enabled": true,
  "last_run_at": "2024-01-01T02:00:00Z",
  "next_run_at": "2024-01-02T02:00:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User doesn't have access to job
- `404 Not Found`: Job not found

**Example**:
```bash
curl http://localhost:8000/api/jobs/job-uuid \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Jobs

List all jobs for a account with pagination.

**Endpoint**: `GET /api/jobs`

**Headers**:
```
Authorization: Bearer <token>
```

**Query Parameters**:
- `account_id` (required): UUID of the account
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 100, max: 1000)
- `enabled` (optional): Filter by enabled status (true/false)

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "job-uuid-1",
      "account_id": "account-uuid",
      "name": "Daily Backup",
      "schedule": "0 2 * * *",
      "type": 1,
      "enabled": true,
      "next_run_at": "2024-01-02T02:00:00Z"
    },
    {
      "id": "job-uuid-2",
      "account_id": "account-uuid",
      "name": "Hourly Sync",
      "schedule": "0 * * * *",
      "type": 1,
      "enabled": true,
      "next_run_at": "2024-01-01T11:00:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 100
}
```

**Example**:
```bash
curl "http://localhost:8000/api/jobs?account_id=account-uuid&limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Job

Update a job's properties.

**Endpoint**: `PUT /api/jobs/{job_id}`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body** (all fields optional):
```json
{
  "name": "Updated Job Name",
  "schedule": "0 3 * * *",
  "type": 2,
  "timezone": "America/New_York",
  "enabled": false
}
```

**Response**: `200 OK`
```json
{
  "id": "job-uuid",
  "account_id": "account-uuid",
  "name": "Updated Job Name",
  "schedule": "0 3 * * *",
  "type": 2,
  "timezone": "America/New_York",
  "enabled": false,
  "next_run_at": "2024-01-02T03:00:00Z",
  "updated_at": "2024-01-01T11:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Invalid cron expression
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User doesn't have access to job
- `404 Not Found`: Job not found

**Example**:
```bash
curl -X PUT http://localhost:8000/api/jobs/job-uuid \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": false
  }'
```

### Delete Job

Delete a job (hard delete).

**Endpoint**: `DELETE /api/jobs/{job_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `204 No Content`

**Errors**:
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User doesn't have access to job
- `404 Not Found`: Job not found

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/jobs/job-uuid \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Enable/Disable Job

Enable or disable a job.

**Endpoint**: `PATCH /api/jobs/{job_id}/enable` or `PATCH /api/jobs/{job_id}/disable`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "id": "job-uuid",
  "enabled": true,
  "updated_at": "2024-01-01T11:00:00Z"
}
```

**Example**:
```bash
# Enable job
curl -X PATCH http://localhost:8000/api/jobs/job-uuid/enable \
  -H "Authorization: Bearer YOUR_TOKEN"

# Disable job
curl -X PATCH http://localhost:8000/api/jobs/job-uuid/disable \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Job Executions

Get execution history for a job.

**Endpoint**: `GET /api/jobs/{job_id}/executions`

**Headers**:
```
Authorization: Bearer <token>
```

**Query Parameters**:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records (default: 100, max: 1000)
- `status` (optional): Filter by status (queued, running, success, failure, timed_out, dead_letter)

**Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "execution-uuid-1",
      "job_id": "job-uuid",
      "status": "success",
      "started_at": "2024-01-01T02:00:00Z",
      "finished_at": "2024-01-01T02:00:05Z",
      "response_code": 200,
      "worker_id": "worker-1",
      "duration_ms": 5000,
      "attempt": 1,
      "created_at": "2024-01-01T02:00:00Z"
    },
    {
      "id": "execution-uuid-2",
      "job_id": "job-uuid",
      "status": "failure",
      "started_at": "2024-01-01T01:00:00Z",
      "finished_at": "2024-01-01T01:00:10Z",
      "error": "Connection timeout",
      "worker_id": "worker-2",
      "duration_ms": 10000,
      "attempt": 1,
      "created_at": "2024-01-01T01:00:00Z"
    }
  ],
  "total": 2,
  "skip": 0,
  "limit": 100
}
```

**Example**:
```bash
# Get all executions
curl http://localhost:8000/api/jobs/job-uuid/executions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get only failed executions
curl "http://localhost:8000/api/jobs/job-uuid/executions?status=failure" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Webhook Management

### Create Webhook

Create a webhook for a job.

**Endpoint**: `POST /webhooks`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "job_id": "job-uuid",
  "url": "https://api.example.com/webhook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer api-key",
    "Content-Type": "application/json"
  },
  "query_params": {
    "param1": "value1"
  },
  "body_template": "{\"action\": \"backup\"}"
}
```

**Fields**:
- `job_id` (required): UUID of the job
- `url` (required): Webhook URL (max 500 characters)
- `method` (required): HTTP method (GET, POST, PUT, DELETE, PATCH)
- `headers` (optional): HTTP headers (JSON object)
- `query_params` (optional): URL query parameters (JSON object)
- `body_template` (optional): Request body template

**Response**: `201 Created`
```json
{
  "id": "webhook-uuid",
  "job_id": "job-uuid",
  "url": "https://api.example.com/webhook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer api-key",
    "Content-Type": "application/json"
  },
  "query_params": {
    "param1": "value1"
  },
  "body_template": "{\"action\": \"backup\"}",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/webhooks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "job-uuid",
    "url": "https://api.example.com/webhook",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer api-key"
    },
    "body_template": "{\"action\": \"backup\"}"
  }'
```

### Get Webhook

Get a webhook by ID.

**Endpoint**: `GET /webhooks/{webhook_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "id": "webhook-uuid",
  "job_id": "job-uuid",
  "url": "https://api.example.com/webhook",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer api-key"
  },
  "query_params": null,
  "body_template": "{\"action\": \"backup\"}",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### Update Webhook

Update a webhook.

**Endpoint**: `PUT /webhooks/{webhook_id}`

**Headers**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body** (all fields optional):
```json
{
  "url": "https://api.example.com/new-webhook",
  "method": "PUT",
  "headers": {
    "Authorization": "Bearer new-api-key"
  },
  "body_template": "{\"action\": \"update\"}"
}
```

**Response**: `200 OK`
```json
{
  "id": "webhook-uuid",
  "job_id": "job-uuid",
  "url": "https://api.example.com/new-webhook",
  "method": "PUT",
  "headers": {
    "Authorization": "Bearer new-api-key"
  },
  "updated_at": "2024-01-01T11:00:00Z"
}
```

### Delete Webhook

Delete a webhook.

**Endpoint**: `DELETE /webhooks/{webhook_id}`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `204 No Content`

## Health & Metrics

### Health Check

Basic health check endpoint.

**Endpoint**: `GET /health`

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "scheduler"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

### Detailed Health Check

Detailed health check with database and Redis connectivity.

**Endpoint**: `GET /health/detailed`

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "scheduler",
  "database": "connected",
  "redis": "connected",
  "scheduler_service": "running"
}
```

**Response** (if unhealthy): `503 Service Unavailable`
```json
{
  "status": "unhealthy",
  "service": "scheduler",
  "database": "disconnected",
  "redis": "connected",
  "scheduler_service": "running"
}
```

### Metrics

Get scheduler metrics (Prometheus-compatible).

**Endpoint**: `GET /metrics`

**Headers**:
```
Authorization: Bearer <token>
```

**Response**: `200 OK`
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "jobs": {
    "total": 100,
    "enabled": 85,
    "disabled": 15
  },
  "executions": {
    "total": 10000,
    "queued": 5,
    "running": 2,
    "success": 9500,
    "failure": 400,
    "dead_letter": 93,
    "success_rate": 95.0,
    "avg_duration_ms": 250.5
  }
}
```

**Example**:
```bash
curl http://localhost:8000/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "ERROR_CODE",
  "status_code": 400
}
```

### Common Error Codes

- `INVALID_CRON_EXPRESSION`: Cron expression is invalid
- `JOB_NOT_FOUND`: Job with given ID not found
- `WEBHOOK_NOT_FOUND`: Webhook with given ID not found
- `UNAUTHORIZED`: Missing or invalid authentication token
- `FORBIDDEN`: User doesn't have access to resource
- `VALIDATION_ERROR`: Request validation failed
- `DATABASE_ERROR`: Database operation failed

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Resource deleted successfully
- `400 Bad Request`: Invalid request (validation error)
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: User doesn't have permission
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service unhealthy

## Code Examples

### Python

```python
import httpx

BASE_URL = "http://localhost:8000"
TOKEN = "your-jwt-token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create a job
response = httpx.post(
    f"{BASE_URL}/api/jobs",
    headers=headers,
    json={
        "account_id": "account-uuid",
        "name": "Daily Backup",
        "schedule": "0 2 * * *",
        "type": 1
    }
)
job = response.json()
print(f"Created job: {job['id']}")

# Create webhook for job
response = httpx.post(
    f"{BASE_URL}/webhooks",
    headers=headers,
    json={
        "job_id": job["id"],
        "url": "https://api.example.com/webhook",
        "method": "POST",
        "headers": {
            "Authorization": "Bearer api-key"
        },
        "body_template": '{"action": "backup"}'
    }
)
webhook = response.json()
print(f"Created webhook: {webhook['id']}")

# Get job executions
response = httpx.get(
    f"{BASE_URL}/api/jobs/{job['id']}/executions",
    headers=headers
)
executions = response.json()
print(f"Found {executions['total']} executions")
```

### JavaScript/TypeScript

```typescript
const BASE_URL = 'http://localhost:8000';
const TOKEN = 'your-jwt-token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// Create a job
const jobResponse = await fetch(`${BASE_URL}/api/jobs`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    account_id: 'account-uuid',
    name: 'Daily Backup',
    schedule: '0 2 * * *',
    type: 1
  })
});
const job = await jobResponse.json();
console.log(`Created job: ${job.id}`);

// Create webhook for job
const webhookResponse = await fetch(`${BASE_URL}/webhooks`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    job_id: job.id,
    url: 'https://api.example.com/webhook',
    method: 'POST',
    headers: {
      'Authorization': 'Bearer api-key'
    },
    body_template: JSON.stringify({ action: 'backup' })
  })
});
const webhook = await webhookResponse.json();
console.log(`Created webhook: ${webhook.id}`);

// Get job executions
const executionsResponse = await fetch(
  `${BASE_URL}/api/jobs/${job.id}/executions`,
  { headers }
);
const executions = await executionsResponse.json();
console.log(`Found ${executions.total} executions`);
```

### cURL

```bash
# Set variables
TOKEN="your-jwt-token"
BASE_URL="http://localhost:8000"

# Create job
JOB_ID=$(curl -s -X POST "$BASE_URL/api/jobs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account-uuid",
    "name": "Daily Backup",
    "schedule": "0 2 * * *",
    "type": 1
  }' | jq -r '.id')

echo "Created job: $JOB_ID"

# Create webhook
WEBHOOK_ID=$(curl -s -X POST "$BASE_URL/webhooks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"url\": \"https://api.example.com/webhook\",
    \"method\": \"POST\",
    \"body_template\": \"{\\\"action\\\": \\\"backup\\\"}\"
  }" | jq -r '.id')

echo "Created webhook: $WEBHOOK_ID"

# Get executions
curl -s "$BASE_URL/api/jobs/$JOB_ID/executions" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Rate Limiting

Currently, rate limiting is not implemented. Future versions may include:
- Per-user rate limits
- Per-endpoint rate limits
- Rate limit headers in responses

## Pagination

List endpoints support pagination via `skip` and `limit` query parameters:

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records (default: 100, max: 1000)

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

## Cron Expression Format

Jobs use standard cron expressions:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

**Examples**:
- `0 2 * * *` - Daily at 2:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Every Sunday at midnight
- `*/15 * * * *` - Every 15 minutes
- `0 0 1 * *` - First day of every month at midnight

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive testing and complete API schema documentation.

