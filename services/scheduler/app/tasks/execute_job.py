"""
Celery task for executing jobs (webhooks).

Handles webhook execution, retries, timeouts, and dead letter queue.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.celery import scheduler as celery_app
from app.models.job_executions import JobExecution
from app.models.jobs import Job
from app.models.webhooks import Webhook
from config.environment import init

# Initialize environment
init()

logger = logging.getLogger(__name__)

# Default retry policy
DEFAULT_RETRY_POLICY = {
    "max_attempts": 3,
    "backoff_seconds": 60,
    "backoff_type": "exponential",  # exponential, linear, fixed
}


class ExecuteJobTask(Task):
    """Custom Celery task class for job execution."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}", exc_info=einfo)
        if args and len(args) > 0:
            execution_id = args[0]
            _update_execution_status(execution_id, "failure", error=str(exc))


@celery_app.task(
    bind=True,
    base=ExecuteJobTask,
    acks_late=True,
    max_retries=0,  # We handle retries manually
    time_limit=300,  # 5 minute timeout
    soft_time_limit=270,  # 4.5 minute soft timeout
)
def execute_job(self, execution_id: str):
    """
    Execute a job (webhook).

    This task:
    1. Loads the job execution, job, and webhook
    2. Executes the webhook
    3. Handles retries based on retry policy
    4. Updates execution status and results
    5. Moves to DLQ if max attempts exceeded

    Args:
        execution_id: Job execution ID
    """
    start_time = time.time()
    db = _get_db_session()
    worker_id = self.request.hostname

    try:
        # Load execution and job
        execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
        if not execution:
            logger.error(f"Job execution {execution_id} not found")
            return

        job = db.query(Job).filter(Job.id == execution.job_id).first()
        if not job:
            logger.error(f"Job {execution.job_id} not found for execution {execution_id}")
            _update_execution_status_in_db(db, execution_id, "failure", error="Job not found")
            return

        # Check if job is still enabled
        if not job.enabled:
            logger.warning(f"Job {job.id} is not enabled")
            _update_execution_status_in_db(db, execution_id, "failure", error="Job is disabled")
            return

        # Get webhook for the job
        webhook = db.query(Webhook).filter(Webhook.job_id == job.id).first()
        if not webhook:
            logger.error(f"Webhook not found for job {job.id}")
            _update_execution_status_in_db(db, execution_id, "failure", error="Webhook not found")
            return

        # Update execution status to running
        _update_execution_status_in_db(db, execution_id, "running", worker_id=worker_id)
        db.commit()

        # Execute the webhook
        try:
            result = _execute_webhook(webhook)
            duration_ms = int((time.time() - start_time) * 1000)

            # Update execution status to success
            _update_execution_status_in_db(
                db,
                execution_id,
                "success",
                worker_id=worker_id,
                duration_ms=duration_ms,
                response=result,
            )
            db.commit()
            logger.info(f"Job {job.id} executed successfully (execution_id: {execution_id}, duration: {duration_ms}ms)")

        except httpx.TimeoutException:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = "Request timed out"
            _handle_execution_failure(db, execution, job, error_msg, duration_ms)

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            _handle_execution_failure(db, execution, job, error_msg, duration_ms)

    except Exception as e:
        logger.error(f"Unexpected error executing job {execution_id}: {e}", exc_info=True)
        _update_execution_status_in_db(db, execution_id, "failure", error=str(e))
        db.commit()
    finally:
        db.close()


def _handle_execution_failure(db: Session, execution: JobExecution, job: Job, error: str, duration_ms: int):
    """
    Handle execution failure with retry logic.

    Args:
        db: Database session
        execution: Job execution instance
        job: Job instance
        error: Error message
        duration_ms: Execution duration in milliseconds
    """
    retry_policy = DEFAULT_RETRY_POLICY
    max_attempts = retry_policy.get("max_attempts", 3)

    if execution.attempt >= max_attempts:
        # Move to dead letter queue
        _update_execution_status_in_db(
            db,
            execution.id,
            "dead_letter",
            duration_ms=duration_ms,
            error=f"Max attempts ({max_attempts}) exceeded. Last error: {error}",
        )
        db.commit()
        logger.error(f"Job {job.id} moved to DLQ after {execution.attempt} attempts")
    else:
        # Schedule retry
        backoff_seconds = _calculate_backoff(execution.attempt, retry_policy)
        retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)

        # Update execution status
        _update_execution_status_in_db(
            db,
            execution.id,
            "failure",
            duration_ms=duration_ms,
            error=error,
        )

        # Create new execution for retry
        new_execution = JobExecution(
            job_id=job.id,
            status="queued",
            attempt=execution.attempt + 1,
        )
        db.add(new_execution)
        db.commit()

        # Enqueue retry task with ETA
        celery_app.send_task(
            "app.tasks.execute_job.execute_job",
            args=[new_execution.id],
            kwargs={},
            eta=retry_at,
        )

        logger.info(
            f"Scheduled retry for job {job.id} (attempt {execution.attempt + 1}/{max_attempts}, "
            f"retry_at: {retry_at})"
        )


def _calculate_backoff(attempt: int, retry_policy: Dict[str, Any]) -> int:
    """
    Calculate backoff delay based on retry policy.

    Args:
        attempt: Current attempt number
        retry_policy: Retry policy configuration

    Returns:
        Backoff delay in seconds
    """
    base_delay = retry_policy.get("backoff_seconds", 60)
    backoff_type = retry_policy.get("backoff_type", "exponential")

    if backoff_type == "exponential":
        return base_delay * (2 ** (attempt - 1))
    elif backoff_type == "linear":
        return base_delay * attempt
    else:  # fixed
        return base_delay


def _execute_webhook(webhook: Webhook) -> str:
    """
    Execute a webhook.

    Args:
        webhook: Webhook instance

    Returns:
        Response text

    Raises:
        Exception: If webhook execution fails
    """
    url = webhook.url
    method = webhook.method.value if hasattr(webhook.method, "value") else str(webhook.method)
    headers = webhook.headers or {}
    query_params = webhook.query_params or {}
    body = webhook.body_template
    timeout = 30  # Default timeout

    # Build URL with query params
    if query_params:
        from urllib.parse import urlencode

        url += "?" + urlencode(query_params)

    with httpx.Client(timeout=timeout) as client:
        response = client.request(method=method, url=url, headers=headers, content=body if body else None)
        response.raise_for_status()
        return response.text


def _update_execution_status(
    execution_id: str,
    status: str,
    worker_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    response: Optional[str] = None,
    error: Optional[str] = None,
):
    """Update execution status (creates new DB session)."""
    db = _get_db_session()
    try:
        _update_execution_status_in_db(db, execution_id, status, worker_id, duration_ms, response, error)
        db.commit()
    finally:
        db.close()


def _update_execution_status_in_db(
    db: Session,
    execution_id: str,
    status: str,
    worker_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    response: Optional[str] = None,
    error: Optional[str] = None,
):
    """Update execution status in database."""
    execution = db.query(JobExecution).filter(JobExecution.id == execution_id).first()
    if execution:
        execution.status = status
        if worker_id:
            execution.worker_id = worker_id
        if duration_ms is not None:
            execution.duration_ms = duration_ms
        if response:
            execution.response_body = response
        if error:
            execution.error = error
        if status == "running":
            execution.started_at = datetime.utcnow()
        elif status in ("success", "failure", "dead_letter", "timed_out"):
            execution.finished_at = datetime.utcnow()


def _get_db_session() -> Session:
    """Get a database session."""
    import os

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
