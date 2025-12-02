"""
Job service for managing CRUD operations on jobs.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.jobs import Job
from app.utils.cron_validator import validate_cron_interval


class JobService:
    """Service class for job-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the job service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_job(
        self,
        name: str,
        account_id: str,
        schedule: str,
        job_type: int,
        timezone: str = "UTC",
        enabled: bool = True,
        user=None,  # Add user parameter
    ) -> Job:
        """
        Create a new job for a account.

        Args:
            account_id: ID of the account this job belongs to
            name: Name of the job
            schedule: Cron expression for scheduling
            job_type: Type identifier for the job
            timezone: Timezone for the schedule (default: UTC)
            enabled: Whether the job is enabled (default: True)
            user: User instance for tier validation (optional)

        Returns:
            Created Job instance

        Raises:
            ValueError: If the cron schedule is invalid or doesn't meet tier requirements
        """
        # Validate cron expression and tier requirements
        validate_cron_interval(self.db, schedule, account_id)

        # Validate cron expression and calculate next run time
        try:
            next_run_at = self._calculate_next_run(schedule, timezone)
        except Exception as e:
            raise ValueError(f"Invalid cron schedule: {str(e)}")

        job = Job(
            id=str(uuid.uuid4()),
            account_id=account_id,
            name=name,
            schedule=schedule,
            type=job_type,
            timezone=timezone,
            enabled=enabled,
            next_run_at=next_run_at,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a specific job by ID.

        Args:
            job_id: ID of the job to retrieve

        Returns:
            Job instance if found, None otherwise
        """
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_jobs_by_account(self, account_id: str, skip: int = 0, limit: int = 100) -> List[Job]:
        """
        Get all jobs for a account with pagination.

        Args:
            account_id: ID of the account
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Job instances
        """
        return self.db.query(Job).filter(Job.account_id == account_id).offset(skip).limit(limit).all()

    def update_job(
        self,
        job_id: str,
        name: Optional[str] = None,
        schedule: Optional[str] = None,
        job_type: Optional[int] = None,
        timezone: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[Job]:
        """
        Update a job's properties.

        Args:
            job_id: ID of the job to update
            name: New name for the job (optional)
            schedule: New cron schedule (optional)
            job_type: New job type (optional)
            timezone: New timezone (optional)
            enabled: New enabled status (optional)
            user: User instance for tier validation (optional)

        Returns:
            Updated Job instance if found, None otherwise

        Raises:
            ValueError: If the new cron schedule is invalid or doesn't meet tier requirements
        """
        job = self.get_job(job_id)
        if not job:
            return None

        # Update fields if provided
        if name is not None:
            job.name = name  # type: ignore[assignment]
        if job_type is not None:
            job.type = job_type  # type: ignore[assignment]
        if timezone is not None:
            job.timezone = timezone  # type: ignore[assignment]
        if enabled is not None:
            job.enabled = enabled  # type: ignore[assignment]

        # If schedule changes, validate and recalculate next_run_at
        if schedule is not None:
            # Validate cron expression and tier requirements
            validate_cron_interval(self.db, schedule, str(job.account_id))

            try:
                job.schedule = schedule  # type: ignore[assignment]
                job.next_run_at = self._calculate_next_run(schedule, job.timezone)  # type: ignore[assignment]
            except Exception as e:
                raise ValueError(f"Invalid cron schedule: {str(e)}")

        self.db.commit()
        self.db.refresh(job)
        return job

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.

        Args:
            job_id: ID of the job to delete

        Returns:
            True if job was deleted, False if not found
        """
        job = self.get_job(job_id)
        if not job:
            return False

        self.db.delete(job)
        self.db.commit()
        return True

    def _calculate_next_run(self, schedule: str, timezone: str = "UTC") -> datetime:
        """
        Calculate the next run time based on cron schedule, with seconds precision.

        Args:
            schedule: Cron expression
            timezone: Timezone for the calculation

        Returns:
            Next run datetime (with seconds level precision)

        Raises:
            Exception: If cron expression is invalid
        """
        from datetime import datetime as dt

        from croniter import croniter

        base_time = dt.utcnow().replace(microsecond=0)
        # Explicitly enable second-level cron schedule support
        cron = croniter(schedule, base_time, ret_type=float)  # get timestamp for seconds-level precision
        next_run_ts = cron.get_next(ret_type=datetime)
        next_run = dt.utcfromtimestamp(next_run_ts)
        if not isinstance(next_run, dt):
            # If cron.get_next returns a float (timestamp), convert to datetime
            next_run = dt.utcfromtimestamp(next_run)
        if not next_run:
            raise ValueError("Invalid cron schedule")
        # ensure no microseconds for seconds-level precision
        return next_run.replace(microsecond=0)


def get_job_service(db: Session) -> JobService:
    """
    Factory function to create a JobService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        JobService instance
    """
    return JobService(db)
