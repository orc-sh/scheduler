# Scheduler Setup Guide

Quick setup guide for the custom scheduler architecture.

## Prerequisites

- Python 3.10+
- MySQL 8.0+
- Redis 7+
- Node.js 18+ (for frontend)

## Quick Start

### 1. Install Dependencies

```bash
cd services/scheduler
pip install -r requirements.txt
```

### 2. Configure Environment

Create `services/scheduler/.env`:

```env
# Database
DATABASE_URL=mysql+pymysql://scheduler_user:scheduler_pass@localhost:3306/job_scheduler

# Redis
REDIS_URL=redis://localhost:6379/0

# Scheduler Service
SCHEDULER_TICK_INTERVAL=5
SCHEDULER_BATCH_SIZE=100

# Authentication (if using Supabase)
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_PUBLIC_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
FRONTEND_URL=http://localhost:5173
```

### 3. Start Infrastructure

```bash
docker-compose up -d mysql redis
```

### 4. Run Database Migrations

```bash
cd services/scheduler

# Create migration (auto-generate from models)
alembic revision --autogenerate -m "Add schedules and schedule_runs tables"

# Apply migration
alembic upgrade head
```

### 5. Start Services

**Terminal 1 - FastAPI**:
```bash
cd services/scheduler
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Scheduler Service**:
```bash
cd services/scheduler
python -m bin.scheduler
# or
./bin/scheduler.sh
```

**Terminal 3 - Celery Worker**:
```bash
cd services/scheduler
celery -A app.celery worker -E -l info
```

**Terminal 4 - Celery Flower (Optional, for monitoring)**:
```bash
cd services/scheduler
celery -A app.celery flower --port=4000
```

### 6. Verify Setup

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Flower**: http://localhost:4000 (if running)

## Creating a Schedule

### Example: Cron Schedule

```bash
curl -X POST http://localhost:8000/api/schedules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Backup",
    "type": "cron",
    "cron_expr": "0 2 * * *",
    "payload": {
      "url": "https://api.example.com/backup",
      "method": "POST",
      "headers": {"Authorization": "Bearer api-key"},
      "body": {"action": "backup"}
    },
    "retry_policy": {
      "max_attempts": 3,
      "backoff_seconds": 60,
      "backoff_type": "exponential"
    },
    "timezone": "UTC"
  }'
```

### Example: Interval Schedule

```bash
curl -X POST http://localhost:8000/api/schedules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Health Check",
    "type": "interval",
    "interval_seconds": 300,
    "payload": {
      "url": "https://api.example.com/health",
      "method": "GET"
    }
  }'
```

### Example: One-off Schedule

```bash
curl -X POST http://localhost:8000/api/schedules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "One-time Task",
    "type": "oneoff",
    "cron_expr": "2024-12-31T23:59:59Z",
    "payload": {
      "url": "https://api.example.com/task",
      "method": "POST"
    }
  }'
```

## Managing Schedules

### List Schedules

```bash
curl http://localhost:8000/api/schedules \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Pause Schedule

```bash
curl -X POST http://localhost:8000/api/schedules/{schedule_id}/pause \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Resume Schedule

```bash
curl -X POST http://localhost:8000/api/schedules/{schedule_id}/resume \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Run Schedule Now

```bash
curl -X POST http://localhost:8000/api/schedules/{schedule_id}/run-now \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### View Execution History

```bash
curl http://localhost:8000/api/schedules/{schedule_id}/runs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### Scheduler Not Enqueuing Tasks

1. Check scheduler logs for errors
2. Verify database connectivity: `GET /health/detailed`
3. Check Redis connectivity
4. Verify schedules have `next_run_at <= now()` and `status = 'active'`

### Tasks Not Executing

1. Check Celery worker logs
2. Verify Redis broker is accessible
3. Check Flower dashboard for task status
4. Verify schedule payload is valid

### Database Connection Issues

1. Verify `DATABASE_URL` is correct
2. Check MySQL is running: `docker-compose ps`
3. Verify database exists: `mysql -u user -p -e "SHOW DATABASES;"`
4. Check connection from Python: `python -c "from db.engine import engine; engine.connect()"`

### Redis Connection Issues

1. Verify `REDIS_URL` is correct
2. Check Redis is running: `docker-compose ps`
3. Test connection: `redis-cli ping`
4. Check Redis logs: `docker-compose logs redis`

## Production Deployment

### Environment Variables

Ensure all required environment variables are set in your deployment environment.

### Scaling

- **Scheduler**: Run 1-2 instances (they coordinate via Redis locks)
- **Celery Workers**: Scale based on task volume (start with 2-4 workers)
- **FastAPI**: Scale horizontally behind load balancer

### Monitoring

- Set up Prometheus to scrape `/metrics` endpoint
- Configure Grafana dashboards
- Set up alerts for:
  - High failure rate
  - Dead letter queue growth
  - Scheduler service down
  - Database connection failures

### Backup

- Regular MySQL backups
- Redis persistence (if storing important state)
- Backup schedule definitions regularly

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture
- Review API documentation at http://localhost:8000/docs
- Set up monitoring and alerting
- Configure production environment variables

