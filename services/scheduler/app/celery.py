import os

from celery import Celery

from config.environment import init

# Initialize environment variables FIRST before importing modules that need them
init()

# Retrieve the DATABASE_URL from environment variables
REDIS_URL = os.getenv("REDIS_URL")

# Create a Celery instance
scheduler = Celery(
    "scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    broker_connection_retry_on_startup=True,
)

# Configure Celery to autodiscover tasks
scheduler.autodiscover_tasks(["app.tasks"], force=True)
