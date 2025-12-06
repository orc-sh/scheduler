"""
Celery worker entry point.
Note: Metrics are exported via the official Grafana celery-exporter service.
"""

import logging
import sys

from config.environment import init

# Initialize environment
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Start Celery worker
    # This is equivalent to: celery -A app.celery.scheduler worker -E --loglevel=info --concurrency=4
    sys.argv = ["celery", "-A", "app.celery.scheduler", "worker", "-E", "--loglevel=info", "--concurrency=4"]

    from celery.__main__ import main

    main()
