#!/usr/bin/env python3
"""
Standalone scheduler service entry point.

This script runs the scheduler service that polls for due schedules
and enqueues them to Celery.

Usage:
    python -m bin.scheduler
    or
    ./bin/scheduler.sh
"""
import logging
import os
import signal
import sys

from app.metrics_server import start_metrics_server
from app.services.scheduler_service import create_scheduler_service
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


def main():
    """Main entry point for scheduler service."""
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set")
        sys.exit(1)

    redis_url = os.getenv("REDIS_URL")
    tick_interval = int(os.getenv("SCHEDULER_TICK_INTERVAL", "5"))
    batch_size = int(os.getenv("SCHEDULER_BATCH_SIZE", "100"))

    # Adaptive polling settings
    adaptive_polling = os.getenv("SCHEDULER_ADAPTIVE_POLLING", "false").lower() == "true"
    min_interval = int(os.getenv("SCHEDULER_MIN_INTERVAL", "1"))
    max_interval = int(os.getenv("SCHEDULER_MAX_INTERVAL", "5"))

    logger.info(
        "Starting scheduler service "
        f"(tick_interval={tick_interval}s, "
        f"batch_size={batch_size}, "
        f"adaptive={adaptive_polling})"
    )

    # Start metrics server
    metrics_port = int(os.getenv("METRICS_PORT", "9091"))
    start_metrics_server(port=metrics_port)

    # Create scheduler service
    scheduler = create_scheduler_service(
        database_url=database_url,
        redis_url=redis_url,
        tick_interval=tick_interval,
        batch_size=batch_size,
        adaptive_polling=adaptive_polling,
        min_interval=min_interval,
        max_interval=max_interval,
    )

    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping scheduler...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start scheduler
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping scheduler...")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
