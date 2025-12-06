"""
Standalone scheduler service that polls for due jobs and enqueues them to Celery.

This service runs as a separate process and is responsible for:
- Polling the database for due jobs
- Acquiring locks to prevent duplicate enqueuing
- Enqueuing tasks to Celery
- Updating next_run_at for jobs
"""

import logging
import time
import uuid
from datetime import datetime
from typing import List, Optional

from redis import Redis
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.celery import scheduler as celery_app
from app.models.job_executions import JobExecution
from app.models.jobs import Job
from app.services.job_service import JobService
from config.environment import init

# Initialize environment
init()

# Import metrics (only if metrics_server is available)
try:
    from app.metrics_server import (
        scheduler_jobs_enqueued_total,
        scheduler_jobs_polled_total,
        scheduler_lock_acquisition_failures_total,
        scheduler_poll_duration_seconds,
    )

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Standalone scheduler service that polls for due jobs.

    Uses polling pattern with configurable tick interval and Redis-based locking
    to prevent duplicate task enqueuing across multiple scheduler instances.
    """

    def __init__(
        self,
        db_session: Session,
        redis_client: Optional[Redis] = None,
        tick_interval: int = 5,
        batch_size: int = 100,
        lock_timeout: int = 30,
        adaptive_polling: bool = False,
        min_interval: int = 1,
        max_interval: int = 5,
    ):
        """
        Initialize the scheduler service.

        Args:
            db_session: SQLAlchemy database session
            redis_client: Redis client for distributed locking (optional)
            tick_interval: Polling interval in seconds (default: 5)
            batch_size: Maximum number of jobs to process per tick (default: 100)
            lock_timeout: Lock timeout in seconds (default: 30)
            adaptive_polling: Enable adaptive polling (default: False)
            min_interval: Minimum polling interval in seconds when adaptive (default: 1)
            max_interval: Maximum polling interval in seconds when adaptive (default: 5)
        """
        self.db = db_session
        self.redis = redis_client
        self.tick_interval = tick_interval
        self.batch_size = batch_size
        self.lock_timeout = lock_timeout
        self.job_service = JobService(db_session)
        self.running = False

        # Adaptive polling settings
        self.adaptive_polling = adaptive_polling
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.current_interval = min_interval if adaptive_polling else tick_interval
        self.consecutive_empty_ticks = 0

    def start(self):
        """Start the scheduler polling loop."""
        self.running = True
        interval_info = (
            f"adaptive (min={self.min_interval}s, max={self.max_interval}s)"
            if self.adaptive_polling
            else f"fixed={self.tick_interval}s"
        )
        logger.info(f"Scheduler service started with {interval_info}")

        while self.running:
            try:
                jobs_found = self.tick()

                # Adaptive polling: adjust interval based on whether jobs were found
                if self.adaptive_polling:
                    if jobs_found:
                        # Reset to minimum interval when jobs are found
                        self.current_interval = self.min_interval
                        self.consecutive_empty_ticks = 0
                    else:
                        # Increase interval when no jobs found (exponential backoff, capped)
                        self.consecutive_empty_ticks += 1
                        # Exponential backoff: 1s -> 2s -> 4s -> 5s (capped)
                        self.current_interval = min(
                            self.min_interval * (2 ** min(self.consecutive_empty_ticks, 2)), self.max_interval
                        )
            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}", exc_info=True)
                # Rollback session if it's in a bad state
                try:
                    self.db.rollback()
                except Exception:
                    pass  # Ignore rollback errors

            time.sleep(self.current_interval)

    def stop(self):
        """Stop the scheduler polling loop."""
        self.running = False
        logger.info("Scheduler service stopped")

    def tick(self) -> bool:
        """
        Single scheduler tick: find due jobs and enqueue them.

        This method:
        1. Queries for due jobs
        2. Attempts to acquire locks for each
        3. Enqueues tasks to Celery
        4. Updates next_run_at

        Returns:
            True if jobs were found and processed, False otherwise
        """
        start_time = time.time()
        now = datetime.utcnow()
        logger.debug(f"Scheduler tick at {now} (interval={self.current_interval}s)")

        # Get due jobs
        due_jobs = self._get_due_jobs(batch_size=self.batch_size)

        if not due_jobs:
            logger.debug("No due jobs found")
            if METRICS_AVAILABLE:
                scheduler_jobs_polled_total.labels(status="none").inc()
                scheduler_poll_duration_seconds.observe(time.time() - start_time)
            return False

        logger.info(f"Found {len(due_jobs)} due jobs")
        if METRICS_AVAILABLE:
            scheduler_jobs_polled_total.labels(status="found").inc(len(due_jobs))

        enqueued_count = 0
        failed_count = 0
        for job in due_jobs:
            try:
                if self._try_claim_and_enqueue(job):
                    enqueued_count += 1
                    if METRICS_AVAILABLE:
                        scheduler_jobs_enqueued_total.labels(status="success").inc()
                else:
                    failed_count += 1
                    if METRICS_AVAILABLE:
                        scheduler_jobs_enqueued_total.labels(status="failed").inc()
            except Exception as e:
                logger.error(f"Error processing job {job.id}: {e}", exc_info=True)
                failed_count += 1
                if METRICS_AVAILABLE:
                    scheduler_jobs_enqueued_total.labels(status="error").inc()

        logger.info(f"Enqueued {enqueued_count} jobs, failed {failed_count}")
        if METRICS_AVAILABLE:
            scheduler_poll_duration_seconds.observe(time.time() - start_time)
        return True

    def _get_due_jobs(self, batch_size: int = 100) -> List[Job]:
        """
        Get jobs that are due for execution.

        Args:
            batch_size: Maximum number of jobs to return

        Returns:
            List of due Job instances
        """
        try:
            now = datetime.utcnow()
            return (
                self.db.query(Job)
                .filter(
                    and_(
                        Job.enabled == True,  # noqa: E712
                        Job.next_run_at <= now,
                    )
                )
                .limit(batch_size)
                .all()
            )
        except Exception as e:
            # If session is in a bad state, rollback and retry once
            logger.warning(f"Error querying due jobs, rolling back session: {e}")
            try:
                self.db.rollback()
                now = datetime.utcnow()
                return (
                    self.db.query(Job)
                    .filter(
                        and_(
                            Job.enabled == True,  # noqa: E712
                            Job.next_run_at <= now,
                        )
                    )
                    .limit(batch_size)
                    .all()
                )
            except Exception as retry_error:
                logger.error(f"Error retrying query after rollback: {retry_error}", exc_info=True)
                return []

    def _try_claim_and_enqueue(self, job: Job) -> bool:
        """
        Try to claim a job and enqueue it to Celery.

        Uses Redis lock if available, otherwise falls back to DB row lock.

        Args:
            job: Job to claim and enqueue

        Returns:
            True if successfully claimed and enqueued, False otherwise
        """
        # Try to acquire lock
        lock_acquired = False
        lock_key = f"scheduler:lock:{job.id}"

        if self.redis:
            # Use Redis distributed lock
            lock_acquired = self._acquire_redis_lock(lock_key)
        else:
            # Use DB row lock (SELECT FOR UPDATE)
            lock_acquired = self._acquire_db_lock(job.id)

        if not lock_acquired:
            logger.debug(f"Could not acquire lock for job {job.id}")
            if METRICS_AVAILABLE:
                scheduler_lock_acquisition_failures_total.inc()
            return False

        try:
            # Double-check job is still due and enabled
            self.db.refresh(job)
            if not job.enabled or (job.next_run_at and job.next_run_at > datetime.utcnow()):
                logger.debug(f"Job {job.id} is no longer due or enabled")
                return False

            # Create job execution record
            execution = JobExecution(
                id=str(uuid.uuid4()),
                job_id=job.id,
                status="queued",
                attempt=1,
            )
            self.db.add(execution)
            self.db.commit()
            self.db.refresh(execution)

            # Update next_run_at BEFORE enqueuing (recalculate based on cron)
            from app.utils.cron_utils import create_croniter

            now = datetime.utcnow()
            cron = create_croniter(str(job.schedule), now)
            next_run = cron.get_next(datetime)
            job.next_run_at = next_run
            job.last_run_at = now
            self.db.commit()
            self.db.refresh(job)

            # Enqueue to Celery
            celery_app.send_task(
                "app.tasks.execute_job.execute_job",
                args=[execution.id],
                kwargs={},
            )

            logger.info(f"Enqueued job {job.id} (execution_id: {execution.id})")
            return True

        except Exception as e:
            logger.error(f"Error enqueuing job {job.id}: {e}", exc_info=True)
            self.db.rollback()
            return False
        finally:
            # Release lock
            if self.redis and lock_acquired:
                self._release_redis_lock(lock_key)

    def _acquire_redis_lock(self, lock_key: str) -> bool:
        """
        Acquire a Redis distributed lock.

        Args:
            lock_key: Lock key

        Returns:
            True if lock acquired, False otherwise
        """
        if not self.redis:
            return False

        try:
            # Try to set lock with expiration
            return bool(self.redis.set(lock_key, "locked", ex=self.lock_timeout, nx=True))
        except Exception as e:
            logger.error(f"Error acquiring Redis lock {lock_key}: {e}")
            return False

    def _release_redis_lock(self, lock_key: str):
        """
        Release a Redis distributed lock.

        Args:
            lock_key: Lock key
        """
        if not self.redis:
            return

        try:
            self.redis.delete(lock_key)
        except Exception as e:
            logger.error(f"Error releasing Redis lock {lock_key}: {e}")

    def _acquire_db_lock(self, job_id: str) -> bool:
        """
        Acquire a DB row lock using SELECT FOR UPDATE.

        Args:
            job_id: Job ID to lock

        Returns:
            True if lock acquired, False otherwise
        """
        try:
            # Use SELECT FOR UPDATE to acquire row lock
            job = self.db.query(Job).filter(Job.id == job_id).with_for_update(nowait=True).first()
            return job is not None
        except Exception:
            # Lock acquisition failed (another process has the lock)
            return False


def create_scheduler_service(
    database_url: str,
    redis_url: Optional[str] = None,
    tick_interval: int = 5,
    batch_size: int = 100,
    adaptive_polling: bool = False,
    min_interval: int = 1,
    max_interval: int = 5,
) -> SchedulerService:
    """
    Factory function to create a SchedulerService instance.

    Args:
        database_url: Database connection URL
        redis_url: Optional Redis connection URL
        tick_interval: Polling interval in seconds (used when adaptive_polling=False)
        batch_size: Maximum jobs per tick
        adaptive_polling: Enable adaptive polling (default: False)
        min_interval: Minimum polling interval in seconds when adaptive (default: 1)
        max_interval: Maximum polling interval in seconds when adaptive (default: 5)

    Returns:
        SchedulerService instance
    """
    from redis import Redis as RedisClient

    # Create DB session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    # Create Redis client if URL provided
    redis_client = None
    if redis_url:
        try:
            redis_client = RedisClient.from_url(redis_url, decode_responses=False)
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Falling back to DB locks.")

    return SchedulerService(
        db_session=db_session,
        redis_client=redis_client,
        tick_interval=tick_interval,
        batch_size=batch_size,
        adaptive_polling=adaptive_polling,
        min_interval=min_interval,
        max_interval=max_interval,
    )
