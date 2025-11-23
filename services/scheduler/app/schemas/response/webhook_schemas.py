"""
Response schemas for webhook operations.
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.response.job_schemas import JobResponse
from app.schemas.response.project_schemas import ProjectResponse


class WebhookResponse(BaseModel):
    """Schema for webhook response"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "url": "https://api.example.com/webhook",
                "method": "POST",
                "headers": {"Authorization": "Bearer token123"},
                "query_params": {"key": "value"},
                "body_template": '{"event": "scheduled"}',
                "content_type": "application/json",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "job": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Daily Report Job",
                    "schedule": "0 9 * * *",
                    "timezone": "UTC",
                    "enabled": True,
                },
            }
        },
    )

    id: str = Field(..., description="Webhook ID")
    job_id: str = Field(..., description="Job ID this webhook belongs to")
    url: str = Field(..., description="URL to send the webhook to")
    method: str = Field(..., description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters")
    body_template: Optional[str] = Field(None, description="Template for the request body")
    content_type: str = Field(..., description="Content type of the request")
    created_at: datetime = Field(..., description="When the webhook was created")
    updated_at: datetime = Field(..., description="When the webhook was last updated")
    job: Optional[JobResponse] = Field(None, description="Associated job information")


class CronWebhookResponse(BaseModel):
    """Schema for Cron webhook creation response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "user_id": "123e4567-e89b-12d3-a456-426614174003",
                    "name": "John Doe",
                    "created_at": "2024-01-01T00:00:00",
                },
                "job": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "project_id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "Daily Report Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "UTC",
                    "enabled": True,
                    "last_run_at": None,
                    "next_run_at": "2024-01-02T09:00:00",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                },
                "webhook": {
                    "id": "123e4567-e89b-12d3-a456-426614174002",
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "content_type": "application/json",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                },
            }
        }
    )

    project: ProjectResponse = Field(..., description="Project details")
    job: JobResponse = Field(..., description="Created job details")
    webhook: WebhookResponse = Field(..., description="Created webhook details")
