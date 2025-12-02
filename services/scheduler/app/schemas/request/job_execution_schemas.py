"""
Request schemas for job execution operations.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class GetJobExecutionsRequest(BaseModel):
    """Schema for query parameters when getting job executions"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "limit": 20,
                "offset": 0,
                "status": "success",
            }
        }
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of executions to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of executions to skip (for pagination)",
    )
    status: Optional[Literal["queued", "running", "success", "failure", "timed_out", "dead_letter"]] = Field(
        None, description="Filter executions by status"
    )
