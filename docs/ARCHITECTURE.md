# Scheduler Architecture & Job Processing

Complete architecture documentation for the Scheduler system, focusing on how jobs are processed from creation to execution.

## Table of Contents

- [System Overview](#system-overview)
- [Core Components](#core-components)
- [Job Processing Flow](#job-processing-flow)
- [Data Models](#data-models)
- [Scheduler Service](#scheduler-service)
- [Execution Engine](#execution-engine)
- [Retry & Dead Letter Queue](#retry--dead-letter-queue)
- [Locking & Concurrency](#locking--concurrency)
- [Multi-Tenancy](#multi-tenancy)
- [Observability](#observability)
- [Deployment & Scaling](#deployment--scaling)

## System Overview

The Scheduler is a distributed system for scheduling and executing webhook-based jobs using cron expressions. It consists of three main components:

1. **API Service (FastAPI)** - REST API for managing jobs and schedules
2. **Scheduler Service** - Standalone process that polls for due jobs and enqueues them
3. **Execution Engine (Celery)** - Worker processes that execute webhook jobs

### Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────┐
│      API Service (FastAPI)          │
│  - Job CRUD operations              │
│  - Authentication & Authorization   │
│  - Health checks & Metrics           │
└──────┬──────────────────────────────┘
       │
       │ Writes to
       ▼
┌─────────────────────────────────────┐
│         MySQL Database               │
│  - Jobs table                        │
│  - Job Executions table              │
│  - Webhooks table                    │
└──────┬───────────────────────────────┘
       │
       │ Polls for due jobs
       ▼
┌─────────────────────────────────────┐
│    Scheduler Service (Standalone)   │
│  - Polls database every N seconds    │
│  - Acquires locks (Redis/DB)         │
│  - Enqueues tasks to Celery          │
│  - Updates next_run_at               │
└──────┬───────────────────────────────┘
       │
       │ Enqueues tasks
       ▼
┌─────────────────────────────────────┐
│         Redis (Broker)              │
│  - Celery task queue                 │
│  - Distributed locks                 │
└──────┬───────────────────────────────┘
       │
       │ Consumes tasks
       ▼
┌─────────────────────────────────────┐
│    Celery Workers (Execution)       │
│  - Execute webhooks                 │
│  - Handle retries                   │
│  - Update execution status          │
└─────────────────────────────────────┘
```

## Core Components

### 1. API Service (FastAPI)

**Location**: `services/scheduler/app/`

**Responsibilities**:
- REST API endpoints for job management
- Authentication and authorization (JWT)
- Input validation and error handling
- Health checks and metrics

**Key Files**:
- `app/main.py` - FastAPI application entry point
- `app/controllers/job_controller.py` - Job management endpoints
- `app/services/job_service.py` - Business logic for jobs
- `app/middleware/auth_middleware.py` - JWT authentication

### 2. Scheduler Service

**Location**: `services/scheduler/app/services/scheduler_service.py`

**Responsibilities**:
- Poll database for due jobs at configurable intervals
- Acquire distributed locks to prevent duplicate enqueuing
- Enqueue tasks to Celery
- Update `next_run_at` for jobs

**Key Features**:
- Polling pattern (configurable tick interval: 1-5 seconds)
- Redis distributed locking (with DB fallback)
- Batch processing (configurable batch size)
- Adaptive polling (adjusts interval based on workload)

### 3. Execution Engine (Celery)

**Location**: `services/scheduler/app/tasks/execute_job.py`

**Responsibilities**:
- Execute webhook HTTP requests
- Handle retries with configurable backoff
- Manage dead letter queue
- Track execution status and metrics

**Key Features**:
- Webhook execution via HTTP
- Retry logic (exponential, linear, fixed backoff)
- Task timeouts (5 min hard, 4.5 min soft)
- Worker tracking and duration metrics

## Job Processing Flow

### Complete Lifecycle

```
1. CREATE JOB
   └─> User creates job via API
   └─> JobService validates cron expression
   └─> Calculates next_run_at
   └─> Stores in database

2. SCHEDULER POLLING
   └─> SchedulerService polls every N seconds
   └─> Queries: WHERE enabled=true AND next_run_at <= NOW()
   └─> Finds due jobs

3. LOCK ACQUISITION
   └─> Attempts Redis lock (or DB row lock)
   └─> Prevents duplicate enqueuing across instances

4. TASK ENQUEUING
   └─> Creates JobExecution record (status: "queued")
   └─> Updates next_run_at (recalculates from cron)
   └─> Enqueues Celery task with execution_id

5. CELERY EXECUTION
   └─> Worker picks up task
   └─> Updates execution status to "running"
   └─> Executes webhook HTTP request
   └─> Updates execution status to "success" or "failure"

6. RETRY HANDLING (if failed)
   └─> Checks attempt < max_attempts
   └─> Calculates backoff delay
   └─> Creates new execution with attempt+1
   └─> Enqueues retry task with ETA

7. DEAD LETTER QUEUE (if max attempts exceeded)
   └─> Updates execution status to "dead_letter"
   └─> Logs error for admin review
```

### Detailed Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Job Creation (API Service)                              │
│    POST /api/jobs                                           │
│    └─> JobService.create_job()                             │
│        ├─> Validates cron expression                        │
│        ├─> Calculates next_run_at                          │
│        └─> Saves to database                                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Scheduler Polling (Scheduler Service)                    │
│    SchedulerService.tick()                                 │
│    └─> _get_due_jobs()                                      │
│        └─> Query: enabled=true AND next_run_at <= NOW()    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Lock Acquisition                                         │
│    _try_claim_and_enqueue()                                 │
│    ├─> Try Redis lock: scheduler:lock:{job_id}            │
│    └─> Fallback: DB row lock (SELECT FOR UPDATE)           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Task Enqueuing                                           │
│    ├─> Create JobExecution (status: "queued")               │
│    ├─> Recalculate next_run_at from cron                    │
│    ├─> Update job.next_run_at                               │
│    └─> celery_app.send_task("execute_job", [execution_id])  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Celery Execution                                         │
│    execute_job(execution_id)                                │
│    ├─> Load JobExecution, Job, Webhook                     │
│    ├─> Update status: "running"                             │
│    ├─> Execute webhook HTTP request                         │
│    └─> Update status: "success" or "failure"                │
└─────────────────────────────────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
              SUCCESS      FAILURE
                    │           │
                    │           ▼
                    │   ┌───────────────────────────────┐
                    │   │ 6. Retry Logic                 │
                    │   │    _handle_execution_failure() │
                    │   │    ├─> Check attempt < max     │
                    │   │    ├─> Calculate backoff       │
                    │   │    ├─> Create new execution    │
                    │   │    └─> Enqueue retry (ETA)    │
                    │   └───────────────────────────────┘
                    │           │
                    │           │ (if max attempts)
                    │           ▼
                    │   ┌───────────────────────────────┐
                    │   │ 7. Dead Letter Queue           │
                    │   │    Update status: "dead_letter"│
                    │   └───────────────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │   Complete    │
            └───────────────┘
```

## Data Models

### Job Model

**Table**: `jobs`

```python
id: UUID (Primary Key)
project_id: UUID (Foreign Key → projects.id)
name: String(255)
schedule: String(50)  # Cron expression (e.g., "0 2 * * *")
type: Integer  # Job type identifier
timezone: String(50)  # Default: "UTC"
enabled: Boolean  # Default: true
last_run_at: TIMESTAMP  # Last execution time
next_run_at: TIMESTAMP  # Next scheduled execution (indexed)
created_at: TIMESTAMP
updated_at: TIMESTAMP
```

**Indexes**:
- `idx_jobs_project_id` on `project_id`
- `idx_jobs_next_run_at` on `next_run_at`
- `idx_jobs_enabled` on `enabled`

**Key Fields**:
- `schedule`: Cron expression (validated using `croniter`)
- `next_run_at`: Precomputed next execution time (used by scheduler for querying)
- `enabled`: Controls whether job is scheduled

### JobExecution Model

**Table**: `job_executions`

```python
id: UUID (Primary Key)
job_id: UUID (Foreign Key → jobs.id)
status: Enum  # queued, running, success, failure, timed_out, dead_letter
started_at: TIMESTAMP
finished_at: TIMESTAMP
response_code: Integer  # HTTP response code
response_body: Text  # Webhook response
worker_id: String(255)  # Celery worker hostname
duration_ms: Integer  # Execution duration
error: Text  # Error message if failed
attempt: Integer  # Retry attempt number (default: 1)
created_at: TIMESTAMP
```

**Indexes**:
- `idx_job_executions_job_id` on `job_id`
- `idx_job_executions_created_at` on `created_at`
- `idx_job_executions_status` on `status`

**Status Flow**:
```
queued → running → success
                → failure → (retry) → queued → ...
                → timed_out
                → dead_letter (max attempts exceeded)
```

### Webhook Model

**Table**: `webhooks`

```python
id: UUID (Primary Key)
job_id: UUID (Foreign Key → jobs.id)
url: String(500)  # Webhook URL
method: Enum  # GET, POST, PUT, DELETE, PATCH
headers: JSON  # HTTP headers
query_params: JSON  # URL query parameters
body_template: Text  # Request body template
```

## Scheduler Service

### Polling Pattern

The scheduler uses a **polling pattern** to find due jobs:

1. **Tick Interval**: Configurable (default: 5 seconds)
   - Environment variable: `SCHEDULER_TICK_INTERVAL`
   - Can be set to 1-5 seconds for responsiveness

2. **Query Pattern**:
   ```sql
   SELECT * FROM jobs
   WHERE enabled = true
     AND next_run_at <= NOW()
   LIMIT batch_size
   ```

3. **Adaptive Polling** (optional):
   - Starts at minimum interval (1s) when jobs are found
   - Exponentially increases interval when no jobs found
   - Caps at maximum interval (5s)
   - Resets to minimum when jobs are found again

### Lock Acquisition

**Purpose**: Prevent multiple scheduler instances from enqueuing the same job.

**Strategy 1: Redis Distributed Lock (Preferred)**

```python
lock_key = f"scheduler:lock:{job_id}"
# Try to acquire lock with expiration
redis.set(lock_key, "locked", ex=30, nx=True)
```

**Pros**:
- Works across multiple scheduler instances
- Fast and lightweight
- Automatic expiration prevents deadlocks

**Cons**:
- Requires Redis
- Clock drift can cause issues (mitigated by short timeouts)

**Strategy 2: DB Row Lock (Fallback)**

```python
# Use SELECT FOR UPDATE NOWAIT
job = db.query(Job).filter(Job.id == job_id)
    .with_for_update(nowait=True).first()
```

**Pros**:
- No external dependencies
- Works with any database supporting row locks

**Cons**:
- Less efficient with many scheduler instances
- Database connection overhead

### Next Run Calculation

When a job is enqueued, the scheduler recalculates `next_run_at`:

```python
from croniter import croniter

now = datetime.utcnow()
cron = croniter(job.schedule, now)
next_run = cron.get_next(datetime)
job.next_run_at = next_run
```

This ensures the job will be picked up on the next scheduled time.

## Execution Engine

### Celery Task

**Task Name**: `app.tasks.execute_job.execute_job`

**Configuration**:
- `acks_late=True` - Task acknowledged after completion
- `max_retries=0` - Manual retry handling (not Celery retries)
- `time_limit=300` - 5 minute hard timeout
- `soft_time_limit=270` - 4.5 minute soft timeout

### Execution Steps

1. **Load Resources**:
   ```python
   execution = db.query(JobExecution).filter(id=execution_id).first()
   job = db.query(Job).filter(id=execution.job_id).first()
   webhook = db.query(Webhook).filter(job_id=job.id).first()
   ```

2. **Update Status**:
   ```python
   execution.status = "running"
   execution.started_at = datetime.utcnow()
   execution.worker_id = self.request.hostname
   ```

3. **Execute Webhook**:
   ```python
   response = httpx.request(
       method=webhook.method,
       url=webhook.url,
       headers=webhook.headers,
       params=webhook.query_params,
       content=webhook.body_template
   )
   ```

4. **Update Result**:
   ```python
   execution.status = "success"
   execution.response_code = response.status_code
   execution.response_body = response.text
   execution.duration_ms = (end_time - start_time) * 1000
   execution.finished_at = datetime.utcnow()
   ```

### Error Handling

- **Timeout**: Catches `httpx.TimeoutException`, updates status to "failure"
- **HTTP Errors**: Catches `httpx.HTTPStatusError`, updates status to "failure"
- **Other Exceptions**: Catches all exceptions, updates status to "failure"

## Retry & Dead Letter Queue

### Retry Policy

Default retry policy (configurable per job):

```json
{
  "max_attempts": 3,
  "backoff_seconds": 60,
  "backoff_type": "exponential"  // exponential, linear, or fixed
}
```

### Backoff Strategies

1. **Exponential**:
   ```
   delay = base_delay * (2 ^ (attempt - 1))
   Example: 60s, 120s, 240s
   ```

2. **Linear**:
   ```
   delay = base_delay * attempt
   Example: 60s, 120s, 180s
   ```

3. **Fixed**:
   ```
   delay = base_delay
   Example: 60s, 60s, 60s
   ```

### Retry Flow

```
Execution fails
    │
    ▼
Check: attempt < max_attempts?
    │
    ├─> YES: Calculate backoff delay
    │       ├─> Create new JobExecution (attempt + 1)
    │       ├─> Enqueue retry task with ETA
    │       └─> Update current execution status: "failure"
    │
    └─> NO: Move to Dead Letter Queue
            └─> Update execution status: "dead_letter"
```

### Dead Letter Queue

Jobs that exceed `max_attempts` are moved to `dead_letter` status:

- **Status**: `dead_letter`
- **Error Message**: Includes all attempt details
- **Recovery**: Can be manually retried (future feature)
- **Monitoring**: Should be alerted on DLQ growth

## Locking & Concurrency

### Scheduler Instances

Multiple scheduler instances can run simultaneously:

- **Coordination**: Redis distributed locks prevent duplicate enqueuing
- **Scalability**: Each instance processes different jobs
- **Fault Tolerance**: If one instance fails, others continue

### Celery Workers

Multiple Celery workers can run simultaneously:

- **Task Distribution**: Celery automatically distributes tasks
- **Concurrency**: Each worker can process multiple tasks (prefetch)
- **Scaling**: Add more workers to increase throughput

### Database Concurrency

- **Row Locks**: Used when Redis unavailable
- **Transaction Isolation**: Ensures consistency
- **Indexes**: Optimize query performance

## Multi-Tenancy

### Current Implementation

- **Tenant ID**: Uses `user_id` as tenant identifier
- **Isolation**: All queries filtered by `user_id`
- **Authorization**: Users can only access their own jobs

### Future Enhancements

- Add `tenants` table for organization-level multi-tenancy
- Add `user_tenant_memberships` table
- Support team/organization-based access control

## Observability

### Health Checks

**Endpoint**: `GET /health`

```json
{
  "status": "healthy",
  "service": "scheduler"
}
```

**Endpoint**: `GET /health/detailed`

```json
{
  "status": "healthy",
  "service": "scheduler",
  "database": "connected",
  "redis": "connected",
  "scheduler_service": "running"
}
```

### Metrics

**Endpoint**: `GET /metrics`

```json
{
  "timestamp": "2024-01-01T00:00:00",
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

### Logging

Structured logging with levels:

- **INFO**: Normal operations (scheduler ticks, task execution)
- **WARNING**: Recoverable issues (lock acquisition failures)
- **ERROR**: Failures (task execution errors, DB connection issues)

### Monitoring Recommendations

- **Prometheus**: Scrape `/metrics` endpoint
- **Grafana**: Create dashboards for:
  - Job execution rates
  - Success/failure rates
  - Dead letter queue size
  - Scheduler tick performance
- **Alerts**: Set up for:
  - High failure rate (> 10%)
  - Dead letter queue growth
  - Scheduler service down
  - Database connection failures

## Deployment & Scaling

### Environment Variables

**Required**:
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/scheduler
REDIS_URL=redis://localhost:6379/0
```

**Optional**:
```env
SCHEDULER_TICK_INTERVAL=5  # Polling interval in seconds
SCHEDULER_BATCH_SIZE=100   # Max jobs per tick
```

### Service Startup

1. **FastAPI**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Scheduler Service**:
   ```bash
   python -m bin.scheduler
   ```

3. **Celery Worker**:
   ```bash
   celery -A app.celery worker -E -l info
   ```

### Scaling Strategy

- **API Service**: Scale horizontally behind load balancer (stateless)
- **Scheduler Service**: Run 1-2 instances (coordinate via Redis locks)
- **Celery Workers**: Scale based on task volume (start with 2-4 workers)

### Production Considerations

1. **Database**:
   - Connection pooling
   - Read replicas for reporting
   - Regular backups

2. **Redis**:
   - Persistence enabled
   - High availability setup
   - Memory monitoring

3. **Monitoring**:
   - Prometheus + Grafana
   - Log aggregation (ELK/Loki)
   - Error tracking (Sentry)

4. **Security**:
   - JWT token validation
   - Rate limiting
   - Input validation
   - SQL injection prevention

## Performance Optimization

### Database

- **Indexes**: Critical indexes on `next_run_at`, `enabled`, `job_id`
- **Query Optimization**: Limit batch size to prevent large queries
- **Connection Pooling**: Reuse database connections

### Scheduler

- **Batch Processing**: Process multiple jobs per tick
- **Adaptive Polling**: Reduce polling frequency when idle
- **Lock Timeout**: Short lock timeouts prevent blocking

### Celery

- **Prefetch Limit**: Control task prefetching
- **Worker Concurrency**: Adjust based on workload
- **Task Routing**: Route different job types to different queues

## Future Enhancements

- Event-driven scheduler (Kafka/Redis Streams)
- Webhook signature verification
- Custom execution environments (Docker containers)
- Schedule templates
- Schedule dependencies
- Timezone-aware scheduling
- Schedule versioning
- Admin dashboard for DLQ management
- Webhook notifications for schedule failures
