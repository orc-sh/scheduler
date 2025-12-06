# Infrastructure Setup

This directory contains all infrastructure configuration files for the scheduler application, organized into application services and monitoring services.

## Structure

```
infra/
├── app/                              # Application services
│   ├── docker-compose.yml            # Application Docker Compose orchestration
│   └── nginx/
│       ├── nginx.conf                # Nginx reverse proxy configuration
│       └── ssl/                      # SSL certificates (not in git)
│
└── monitor/                          # Monitoring services
    ├── docker-compose.yml            # Monitoring Docker Compose orchestration
    ├── prometheus/
    │   ├── prometheus.yml            # Prometheus configuration
    │   └── alerts.yml                # Alert rules
    ├── grafana/
    │   ├── provisioning/
    │   │   ├── datasources/          # Prometheus datasource config
    │   │   └── dashboards/           # Dashboard provisioning config
    │   └── dashboards/               # Grafana dashboard JSON files
    └── alertmanager/
        └── config.yml                # Alert Manager configuration
```

## Quick Start

### 1. Start Application Services

First, start the application services (database, Redis, API services, workers):

```bash
cd infra/app
docker-compose up -d
```

This will start:
- MySQL database
- Redis cache
- Scheduler API service
- Auth service
- Celery worker
- Celery exporter (Grafana celery-exporter for Prometheus metrics)
- Scheduler worker
- Nginx reverse proxy
- Metrics exporters (Redis, MySQL, Node)

### 2. Start Monitoring Services

After the application services are running, start the monitoring stack:

```bash
cd infra/monitor
docker-compose up -d
```

This will start:
- Prometheus (metrics collection)
- Grafana (visualization)
- Alert Manager (alert routing)

### 3. Access Services

- **Application:**
  - Scheduler API: http://localhost:8000
  - Auth API: http://localhost:8001
  - API Docs: http://localhost:8000/docs
  - Nginx: http://localhost:80

- **Monitoring:**
  - Prometheus: http://localhost:9090
  - Grafana: http://localhost:3000 (admin/admin)
  - Alert Manager: http://localhost:9093

## Services Overview

### Application Services (`infra/app/`)

**Core Services:**
- **scheduler**: FastAPI scheduler service (port 8000)
- **auth**: FastAPI authentication service (port 8001)
- **celery_worker**: Celery worker for task execution
- **celery_exporter**: Official Grafana celery-exporter for Prometheus metrics (port 9808)
- **scheduler_worker**: Standalone scheduler polling service (metrics on port 9091)
- **nginx**: Reverse proxy and load balancer (ports 80, 443)

**Infrastructure:**
- **mysql**: MySQL database (port 3307)
- **redis**: Redis cache and message broker (port 6379)

**Metrics Exporters:**
- **redis_exporter**: Redis metrics exporter (port 9121)
- **mysql_exporter**: MySQL metrics exporter (port 9104)
- **node_exporter**: System metrics exporter (port 9100)

### Monitoring Services (`infra/monitor/`)

**Monitoring Stack:**
- **prometheus**: Metrics collection and alerting (port 9090)
- **grafana**: Visualization and dashboards (port 3000)
- **alertmanager**: Alert routing and notifications (port 9093)

## Metrics Endpoints

All application services expose Prometheus metrics on `/metrics`:

- Scheduler API: http://localhost:8000/metrics
- Auth API: http://localhost:8001/metrics
- Scheduler Worker: http://localhost:9091/metrics
- Celery Exporter: http://localhost:9808/metrics

## Grafana Dashboards

Grafana dashboards are automatically provisioned from `monitor/grafana/dashboards/`:

- **Scheduler Dashboard**: Job execution metrics, success/failure rates, execution times
- **Celery Worker Dashboard**: Task queue metrics, worker health, task execution stats
- **System Dashboard**: CPU, memory, disk usage

Access dashboards at http://localhost:3000 after logging in.

## Prometheus Alerts

Prometheus alerts are configured in `monitor/prometheus/alerts.yml`:

- High job failure rate
- Critical job failure rate
- Scheduler worker down
- Celery worker down
- High task queue length
- Service unavailability
- High resource usage (CPU, memory)

Configure notification channels in `monitor/alertmanager/config.yml`.

## Environment Variables

Environment variables can be set in `.env` files or passed directly. Key variables:

**Application:**
- `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`
- `REDIS_PORT`
- `SCHEDULER_PORT`, `AUTH_PORT`
- `SCHEDULER_TICK_INTERVAL`, `SCHEDULER_BATCH_SIZE`

**Monitoring:**
- `PROMETHEUS_PORT` (default: 9090)
- `GRAFANA_PORT` (default: 3000)
- `ALERTMANAGER_PORT` (default: 9093)
- `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`

## SSL Certificates

For production, place SSL certificates in `app/nginx/ssl/`:
- `cert.pem`: SSL certificate
- `key.pem`: SSL private key

For development, you can generate self-signed certificates:
```bash
mkdir -p infra/app/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout infra/app/nginx/ssl/key.pem \
  -out infra/app/nginx/ssl/cert.pem
```

## Usage Examples

### Start Everything

```bash
# Start application services
cd infra/app
docker-compose up -d

# Start monitoring services
cd ../monitor
docker-compose up -d
```

### Stop Services

```bash
# Stop monitoring services
cd infra/monitor
docker-compose down

# Stop application services
cd ../app
docker-compose down
```

### View Logs

```bash
# Application services
cd infra/app
docker-compose logs -f [service_name]

# Monitoring services
cd infra/monitor
docker-compose logs -f [service_name]
```

### Restart a Service

```bash
# Application service
cd infra/app
docker-compose restart [service_name]

# Monitoring service
cd infra/monitor
docker-compose restart [service_name]
```

## Network Configuration

Both compose files use the shared `scheduler_network` (created as `infra_scheduler_network` by the application compose file). The monitoring services connect to this network to scrape metrics from application services.

## Troubleshooting

### Check Service Status

```bash
# Application services
cd infra/app
docker-compose ps

# Monitoring services
cd infra/monitor
docker-compose ps
```

### Verify Metrics Endpoints

```bash
# Test metrics endpoints
curl http://localhost:8000/metrics
curl http://localhost:8001/metrics
curl http://localhost:9091/metrics
curl http://localhost:9808/metrics  # Celery exporter
```

### Check Prometheus Targets

Navigate to http://localhost:9090/targets to see which services Prometheus is successfully scraping.

### View Service Logs

```bash
# Application logs
cd infra/app
docker-compose logs -f scheduler
docker-compose logs -f celery_worker

# Monitoring logs
cd infra/monitor
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

### Network Issues

If monitoring services can't connect to application services:

1. Verify the network exists:
   ```bash
   docker network ls | grep scheduler
   ```

2. Ensure application services are running:
   ```bash
   cd infra/app
   docker-compose ps
   ```

3. Check network connectivity:
   ```bash
   docker exec scheduler_prometheus ping -c 2 scheduler_api
   ```

## Development vs Production

**Development:**
- Use HTTP only (no SSL required)
- Default credentials are acceptable
- All services run locally

**Production:**
- Configure SSL certificates in `app/nginx/ssl/`
- Change all default passwords
- Configure proper alert notification channels
- Set up proper backup strategies for volumes
- Use environment-specific `.env` files

## Volumes

**Application volumes:**
- `mysql_data`: MySQL database data
- `redis_data`: Redis persistence data

**Monitoring volumes:**
- `prometheus_data`: Prometheus time-series data (30-day retention)
- `alertmanager_data`: Alert Manager state
- `grafana_data`: Grafana dashboards and configuration

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alert Manager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
