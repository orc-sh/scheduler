"""
Response schemas for job execution operations.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class JobExecutionResponse(BaseModel):
    """Schema for job execution response"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "success",
                "started_at": "2024-01-01T09:00:00",
                "finished_at": "2024-01-01T09:00:05",
                "response_code": 200,
                "response_body": '{"status": "ok"}',
                "worker_id": "celery@worker-1",
                "duration_ms": 5000,
                "error": None,
                "attempt": 1,
                "created_at": "2024-01-01T09:00:00",
            }
        },
    )

    id: str = Field(..., description="Job execution ID")
    job_id: str = Field(..., description="Job ID this execution belongs to")
    status: Literal["queued", "running", "success", "failure", "timed_out", "dead_letter"] = Field(
        ..., description="Execution status"
    )
    started_at: Optional[datetime] = Field(None, description="When the execution started")
    finished_at: Optional[datetime] = Field(None, description="When the execution finished")
    response_code: Optional[int] = Field(None, description="HTTP response code from the webhook call")
    response_body: Optional[str] = Field(None, description="Response body from the webhook call")
    worker_id: Optional[str] = Field(None, description="Celery worker that executed the job")
    duration_ms: Optional[int] = Field(None, description="Execution duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if the execution failed")
    attempt: int = Field(..., description="Retry attempt number")
    created_at: datetime = Field(..., description="When the execution was created")
