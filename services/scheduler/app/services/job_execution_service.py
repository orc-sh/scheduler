from typing import List

from sqlalchemy.orm import Session

from app.models.job_executions import JobExecution


class JobExecutionService:
    def __init__(self, db: Session):
        self.db = db

    def get_executions_by_job_id(self, job_id: str, limit: int = 20, offset: int = 0) -> List[JobExecution]:
        """
        Fetch job executions for a given job ID with lazy loading (pagination).

        Args:
            job_id: str - The ID of the job.
            limit: int - Maximum number of records to return. Defaults to 20.
            offset: int - Number of records to skip (for pagination). Defaults to 0.

        Returns:
            List[JobExecution]: A list of JobExecution instances.
        """
        return (
            self.db.query(JobExecution)
            .filter(JobExecution.job_id == job_id)
            .order_by(JobExecution.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )


def get_job_execution_service(db: Session) -> JobExecutionService:
    """
    Factory method to get JobExecutionService instance.

    Args:
        db: SQLAlchemy Session

    Returns:
        JobExecutionService instance
    """
    return JobExecutionService(db)
