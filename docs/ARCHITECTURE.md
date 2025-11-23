# Custom Scheduler Architecture

Complete architecture blueprint for a user-facing scheduling platform (cronhooks-like) using FastAPI, Celery, MySQL (SQLAlchemy), Redis, and React for the dashboard.

## Table of Contents

- [Goals](#goals)
- [Non-goals](#non-goals)
- [High-level Components](#high-level-components)
- [Data Model](#data-model)
- [Scheduler Design Patterns](#scheduler-design-patterns)
- [Locking Strategies](#locking-strategies)
- [Retry and Dead Letter Queue](#retry-and-dead-letter-queue)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Observability](#observability)

## Goals

- ✅ Allow users to create, edit, pause/resume, and delete schedules (cron/interval/one-off)
- ✅ Persist schedules and execution history to a relational DB (MySQL)
- ✅ Use Celery as an execution engine (task workers) — not the scheduler
- ✅ Support multi-tenant use, high scale (thousands of schedules), and strong operational observability
- ✅ Provide robust retry, DLQ, and audit logs for each execution

## Non-goals

- Replacing full orchestration systems like Temporal or Airflow. This is a lightweight SaaS scheduler focused on webhook-style jobs and simple user-defined tasks.

## High-level Components

### 1. API Service (FastAPI)

**Location**: `services/scheduler/app/`

- Public REST API for managing schedules, viewing logs, and controlling runs
- Authentication (Supabase / JWT / OAuth) and tenant isolation
- Exposes endpoints that the UI uses and also internal endpoints for admin operations
- **Main Entry Point**: `app/main.py`
- **Controllers**: `app/controllers/schedule_controller.py`

### 2. Scheduler Service (Standalone Process)

**Location**: `services/scheduler/app/services/scheduler_service.py`

- Small, horizontally-scalable process responsible for computing due jobs and enqueuing them into Celery
- Written in Python, uses SQLAlchemy to read/write the DB, and Redis (or DB) for lightweight locks
- Runs at a configurable tick (e.g., every 1–5 seconds) using polling pattern
- **Entry Point**: `bin/scheduler.py` or `bin/scheduler.sh`

**Key Features**:
- Polls database for due schedules every N seconds (configurable)
- Uses Redis distributed locks or DB row locks to prevent duplicate enqueuing
- Updates `next_run_at` before enqueuing to Celery
- Creates `ScheduleRun` records with status `QUEUED`

### 3. Execution Engine — Celery Workers

**Location**: `services/scheduler/app/tasks/execute_schedule.py`

- Receives tasks from the scheduler and executes them (HTTP webhooks, scripts, lambda-style code executions)
- Responsible for retries, basic timeout control, and writing run results to DB
- **Task**: `app.tasks.execute_schedule.execute_schedule`

**Key Features**:
- Executes webhooks based on schedule payload
- Handles retries with configurable backoff strategies
- Moves failed runs to Dead Letter Queue after max attempts
- Updates run status and duration
- Supports task timeouts (5 minute hard, 4.5 minute soft)

### 4. MySQL (Primary Store)

**Location**: Database models in `app/models/`

- Stores schedules, schedule metadata, run history (logs), tenant metadata, and user settings
- **Models**:
  - `Schedule`: Schedule definitions
  - `ScheduleRun`: Execution history

### 5. Redis

- Broker for Celery tasks
- Optional distributed locking (Redlock) for scheduler coordination
- Short-lived caches

### 6. React Dashboard

**Location**: `apps/web/`

- CRUD for schedules
- Run history viewer
- Monitoring dashboard
- Per-tenant quotas and usage
- Actions (run now, pause, resume)

### 7. Admin/Operator Tools

- Health endpoints (`/health`, `/health/detailed`)
- Metrics endpoint (`/metrics`)
- Maintenance endpoints to re-enqueue stuck jobs (future)

### 8. Observability

- Prometheus-compatible metrics via `/metrics` endpoint
- Health check endpoints
- Centralized logs (structured logging)
- Error tracking (Sentry integration ready)
- Tracing (OpenTelemetry ready)

## Data Model

### `schedules` Table

```python
id (UUID) - Primary key
tenant_id (UUID) - Multi-tenant isolation
user_id (UUID) - User who created the schedule
name (string) - Schedule name
type (enum: cron | interval | oneoff) - Schedule type
cron_expr (string, nullable) - Cron expression (for cron/oneoff)
interval_seconds (int, nullable) - Interval in seconds (for interval)
next_run_at (datetime, indexed) - Next scheduled execution time
last_run_at (datetime) - Last execution time
status (enum: active | paused | deleted) - Schedule status
payload (JSON) - Arbitrary metadata for execution (webhook config, etc.)
retry_policy (JSON) - Retry configuration
created_at, updated_at - Timestamps
```

**Indexes**:
- `idx_schedules_tenant_status` on (tenant_id, status)
- `idx_schedules_next_run_status` on (next_run_at, status)
- `idx_schedules_user_id` on (user_id)

### `schedule_runs` Table

```python
id (UUID) - Primary key
schedule_id (UUID) - Foreign key to schedules
tenant_id (UUID) - Multi-tenant isolation
run_at (datetime, indexed) - Scheduled run time
status (enum: queued | running | success | failed | timed_out | dead_letter)
worker_id (string) - Celery worker that executed the run
duration_ms (int) - Execution duration in milliseconds
response (text) - Webhook response or execution output
error (text) - Error message if failed
attempt (int) - Retry attempt number
created_at, updated_at - Timestamps
```

**Indexes**:
- `idx_schedule_runs_schedule_id` on (schedule_id)
- `idx_schedule_runs_run_at` on (run_at)
- `idx_schedule_runs_tenant_status` on (tenant_id, status)
- `idx_schedule_runs_schedule_run_at` on (schedule_id, run_at)

## Scheduler Design Patterns

### Polling Scheduler (Implemented)

**Pattern**: Scheduler wakes every tick (1–5s default).

**Process**:
1. Query DB: `SELECT * FROM schedules WHERE status='active' AND next_run_at <= now()`
2. Acquire lock per schedule (Redis lock or DB row lock) to avoid double-enqueue
3. Enqueue Celery task with `schedule_id` and `payload`
4. Update `next_run_at` using `croniter` or interval calculation BEFORE commit
5. Insert a `schedule_runs` record with status `'queued'`

**Pros**:
- Simple, easy to reason about
- DB is the source of truth
- Crash recovery is automatic (missed runs will be picked up on next tick)

**Cons**:
- Polling overhead at very large scale
- Must tune tick, batching, and lock handling

**Configuration**:
- `SCHEDULER_TICK_INTERVAL`: Polling interval in seconds (default: 5)
- `SCHEDULER_BATCH_SIZE`: Maximum schedules to process per tick (default: 100)

## Locking Strategies

### Redis Distributed Lock (Preferred)

**Implementation**: `SchedulerService._acquire_redis_lock()`

- Uses Redis `SET key value EX timeout NX` for atomic lock acquisition
- Lock timeout: 30 seconds (configurable)
- Prevents multiple scheduler instances from enqueuing the same schedule

**Pros**:
- Works well with multiple scheduler instances
- Fast and lightweight
- Automatic expiration prevents deadlocks

**Cons**:
- Requires Redis
- Clock drift can cause issues (mitigated by short timeouts)

### DB Row Lock (Fallback)

**Implementation**: `SchedulerService._acquire_db_lock()`

- Uses `SELECT ... FOR UPDATE NOWAIT` to acquire row-level lock
- Fails immediately if another process has the lock

**Pros**:
- No external dependencies
- Works with any database that supports row locks

**Cons**:
- Less efficient with many scheduler instances
- Database connection overhead

## Retry and Dead Letter Queue

### Retry Policy

Each schedule can have a custom retry policy:

```json
{
  "max_attempts": 3,
  "backoff_seconds": 60,
  "backoff_type": "exponential"  // exponential, linear, or fixed
}
```

**Backoff Types**:
- `exponential`: `base_delay * (2 ^ (attempt - 1))`
- `linear`: `base_delay * attempt`
- `fixed`: `base_delay`

### Retry Flow

1. When a run fails, `execute_schedule` task catches the exception
2. Checks if `attempt < max_attempts`
3. If yes:
   - Calculates backoff delay
   - Creates new `ScheduleRun` with `attempt + 1` and `run_at = now + backoff`
   - Enqueues retry task with ETA
4. If no:
   - Updates run status to `DEAD_LETTER`
   - Logs error for admin review

### Dead Letter Queue

Runs that exceed `max_attempts` are moved to `DEAD_LETTER` status. These can be:
- Viewed via API: `GET /api/schedules/{schedule_id}/runs?status=dead_letter`
- Manually retried (future feature)
- Alerted via webhook (future feature)

## API Endpoints

### Schedule Management

- `POST /api/schedules` - Create a new schedule
- `GET /api/schedules` - List schedules (with filtering)
- `GET /api/schedules/{schedule_id}` - Get schedule details
- `PUT /api/schedules/{schedule_id}` - Update schedule
- `DELETE /api/schedules/{schedule_id}` - Delete schedule (soft delete)
- `POST /api/schedules/{schedule_id}/pause` - Pause schedule
- `POST /api/schedules/{schedule_id}/resume` - Resume schedule
- `POST /api/schedules/{schedule_id}/run-now` - Trigger immediate execution
- `GET /api/schedules/{schedule_id}/runs` - Get execution history

### Health & Observability

- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with DB connectivity and metrics
- `GET /metrics` - Scheduler metrics (Prometheus-compatible)

## Deployment

### Environment Variables

**Scheduler Service**:
```bash
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/scheduler
REDIS_URL=redis://localhost:6379/0
SCHEDULER_TICK_INTERVAL=5  # seconds
SCHEDULER_BATCH_SIZE=100
```

**FastAPI Service**:
```bash
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/scheduler
REDIS_URL=redis://localhost:6379/0
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_PUBLIC_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
FRONTEND_URL=http://localhost:5173
```

**Celery Worker**:
```bash
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/scheduler
REDIS_URL=redis://localhost:6379/0
```

### Running the Services

1. **Start Infrastructure**:
   ```bash
   docker-compose up -d mysql redis
   ```

2. **Run Database Migrations**:
   ```bash
   cd services/scheduler
   alembic upgrade head
   ```

3. **Start FastAPI**:
   ```bash
   cd services/scheduler
   uvicorn app.main:app --reload --port 8000
   ```

4. **Start Scheduler Service**:
   ```bash
   cd services/scheduler
   python -m bin.scheduler
   # or
   ./bin/scheduler.sh
   ```

5. **Start Celery Worker**:
   ```bash
   cd services/scheduler
   celery -A app.celery worker -E -l info
   ```

6. **Start Celery Flower (Monitoring)**:
   ```bash
   cd services/scheduler
   celery -A app.celery flower --port=4000
   ```

### Scaling

- **Scheduler Service**: Can run multiple instances (they coordinate via Redis locks)
- **Celery Workers**: Scale horizontally by adding more worker processes/containers
- **FastAPI**: Scale horizontally behind a load balancer (stateless)

## Observability

### Metrics Endpoint

`GET /metrics` returns:

```json
{
  "timestamp": "2024-01-01T00:00:00",
  "schedules": {
    "total": 100,
    "active": 85,
    "paused": 10,
    "deleted": 5
  },
  "runs": {
    "total": 10000,
    "queued": 5,
    "running": 2,
    "success": 9500,
    "failed": 400,
    "dead_letter": 93,
    "success_rate": 95.0,
    "avg_duration_ms": 250.5
  }
}
```

### Health Checks

- `GET /health`: Basic liveness check
- `GET /health/detailed`: Includes database connectivity and basic metrics

### Logging

Structured logging with levels:
- `INFO`: Normal operations (scheduler ticks, task execution)
- `WARNING`: Recoverable issues (lock acquisition failures)
- `ERROR`: Failures (task execution errors, DB connection issues)

### Future Enhancements

- Prometheus exporter for `/metrics` endpoint
- Grafana dashboards
- Sentry integration for error tracking
- OpenTelemetry tracing
- Centralized logging (ELK/Loki)

## Multi-Tenancy

Currently, tenant isolation is implemented using `user_id` as `tenant_id` (single tenant per user). For true multi-tenancy:

1. Add `tenants` table
2. Add `user_tenant_memberships` table
3. Update `_get_tenant_id()` in `schedule_controller.py` to resolve tenant from user's organization
4. Add tenant-level quotas and rate limiting

## Security Considerations

- All API endpoints require JWT authentication
- Tenant isolation enforced at service layer
- Users can only access their own schedules
- Soft deletes prevent accidental data loss
- Input validation on all schedule creation/updates

## Performance Considerations

- Indexes on critical query paths (`next_run_at`, `status`, `tenant_id`)
- Batch processing in scheduler (configurable batch size)
- Connection pooling for database
- Redis connection pooling
- Celery task prefetch limits to prevent worker overload

## Future Enhancements

- Event-driven scheduler (Kafka/Redis Streams)
- Webhook signature verification
- Custom execution environments (Docker containers, Lambda functions)
- Schedule templates
- Schedule dependencies
- Timezone-aware scheduling
- Schedule versioning
- Admin dashboard for DLQ management
- Webhook notifications for schedule failures

