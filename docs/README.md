# Scheduler Documentation

Complete documentation for the Scheduler system.

## 📚 Documentation Files

### 1. [ARCHITECTURE.md](./ARCHITECTURE.md)
**Complete architecture and job processing documentation**

Covers:
- System overview and component architecture
- **Complete job processing flow** (from creation to execution)
- Data models and database schema
- Scheduler service implementation
- Execution engine (Celery) details
- Retry and dead letter queue handling
- Locking and concurrency strategies
- Multi-tenancy
- Observability and monitoring
- Deployment and scaling strategies

### 2. [API_REFERENCE.md](./API_REFERENCE.md)
**Complete API endpoint documentation**

Covers:
- All API endpoints with request/response formats
- Authentication and authorization
- Job management endpoints
- Webhook management endpoints
- Health checks and metrics
- Error handling
- Code examples (Python, JavaScript, cURL)
- Cron expression format

## 🚀 Quick Start

1. **Read** [ARCHITECTURE.md](./ARCHITECTURE.md) to understand how the system works
2. **Reference** [API_REFERENCE.md](./API_REFERENCE.md) when building integrations
3. **Explore** the interactive API docs at http://localhost:8000/docs (when running)

## 📖 Key Topics

### Job Processing Flow

The scheduler processes jobs through these stages:

1. **Job Creation** → User creates job via API
2. **Scheduler Polling** → Scheduler finds due jobs
3. **Lock Acquisition** → Prevents duplicate enqueuing
4. **Task Enqueuing** → Creates execution and enqueues to Celery
5. **Execution** → Celery worker executes webhook
6. **Retry Handling** → Automatic retries on failure
7. **Dead Letter Queue** → Failed jobs after max attempts

See [ARCHITECTURE.md](./ARCHITECTURE.md#job-processing-flow) for detailed flow diagrams.

### API Usage

All endpoints require JWT authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/jobs
```

See [API_REFERENCE.md](./API_REFERENCE.md) for complete endpoint documentation.

## 🔗 Additional Resources

- **Interactive API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## 📝 Documentation Structure

This documentation is organized into two main files:

- **ARCHITECTURE.md**: System design, job processing, and implementation details
- **API_REFERENCE.md**: Complete API documentation with examples

All other documentation has been consolidated into these two files for easier maintenance and reference.
