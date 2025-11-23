"""
Health and observability endpoints.
"""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.job_executions import JobExecution
from app.models.jobs import Job
from db.client import client

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Basic health check endpoint.

    Returns:
        Health status
    """
    return {"status": "OK", "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/detailed")
def detailed_health_check(db: Session = Depends(client)):
    """
    Detailed health check with database connectivity and metrics.

    Returns:
        Detailed health status including database connectivity and basic metrics
    """
    try:
        # Test database connectivity
        db.execute(func.select(1))
        db_status = "connected"

        # Get basic metrics
        total_jobs = db.query(Job).count()
        active_jobs = db.query(Job).filter(Job.enabled == True).count()  # noqa: E712
        total_executions = db.query(JobExecution).count()
        failed_executions = db.query(JobExecution).filter(JobExecution.status == "failure").count()
        dead_letter_executions = db.query(JobExecution).filter(JobExecution.status == "dead_letter").count()

        return {
            "status": "OK",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_status,
            "metrics": {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "total_executions": total_executions,
                "failed_executions": failed_executions,
                "dead_letter_executions": dead_letter_executions,
            },
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/metrics")
def get_metrics(db: Session = Depends(client)) -> Dict:
    """
    Get scheduler metrics for observability.

    Returns:
        Dictionary with scheduler metrics
    """
    try:
        # Job metrics
        total_jobs = db.query(Job).count()
        active_jobs = db.query(Job).filter(Job.enabled == True).count()  # noqa: E712
        disabled_jobs = db.query(Job).filter(Job.enabled == False).count()  # noqa: E712

        # Execution metrics
        total_executions = db.query(JobExecution).count()
        queued_executions = db.query(JobExecution).filter(JobExecution.status == "queued").count()
        running_executions = db.query(JobExecution).filter(JobExecution.status == "running").count()
        success_executions = db.query(JobExecution).filter(JobExecution.status == "success").count()
        failed_executions = db.query(JobExecution).filter(JobExecution.status == "failure").count()
        dead_letter_executions = db.query(JobExecution).filter(JobExecution.status == "dead_letter").count()

        # Calculate success rate
        completed_executions = success_executions + failed_executions + dead_letter_executions
        success_rate = (success_executions / completed_executions * 100) if completed_executions > 0 else 0

        # Average duration (for successful executions)
        avg_duration = (
            db.query(func.avg(JobExecution.duration_ms))
            .filter(JobExecution.status == "success", JobExecution.duration_ms.isnot(None))
            .scalar()
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "jobs": {
                "total": total_jobs,
                "active": active_jobs,
                "disabled": disabled_jobs,
            },
            "executions": {
                "total": total_executions,
                "queued": queued_executions,
                "running": running_executions,
                "success": success_executions,
                "failed": failed_executions,
                "dead_letter": dead_letter_executions,
                "success_rate": round(success_rate, 2),
                "avg_duration_ms": round(avg_duration, 2) if avg_duration else None,
            },
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
