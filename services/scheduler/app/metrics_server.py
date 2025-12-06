"""
Prometheus metrics server for scheduler worker.
Exposes metrics on port 9091.
"""

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)

# Metrics for scheduler worker
scheduler_jobs_polled_total = Counter("scheduler_jobs_polled_total", "Total number of jobs polled", ["status"])

scheduler_jobs_enqueued_total = Counter(
    "scheduler_jobs_enqueued_total", "Total number of jobs enqueued to Celery", ["status"]
)

scheduler_poll_duration_seconds = Histogram(
    "scheduler_poll_duration_seconds", "Time spent polling for jobs", buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

scheduler_lock_acquisition_failures_total = Counter(
    "scheduler_lock_acquisition_failures_total", "Total number of lock acquisition failures"
)

scheduler_worker_up = Gauge("scheduler_worker_up", "Scheduler worker is running (1) or not (0)")

scheduler_worker_up.set(1)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_metrics_server(port=9091):
    """Start the Prometheus metrics server in a background thread."""
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Metrics server started on port {port}")
    return server
