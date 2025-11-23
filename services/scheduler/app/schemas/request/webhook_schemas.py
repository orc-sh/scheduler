"""
Request schemas for webhook operations.
"""

from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.request.job_schemas import CreateJobRequest, UpdateJobRequest


class CreateWebhookRequest(BaseModel):
    """Schema for creating a new webhook"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://api.example.com/webhook",
                "method": "POST",
                "headers": {"Authorization": "Bearer token123"},
                "query_params": {"key": "value"},
                "body_template": '{"event": "scheduled", "data": "{{data}}"}',
                "content_type": "application/json",
            }
        }
    )

    url: str = Field(..., description="URL to send the webhook to", min_length=1, max_length=1024)
    method: str = Field(default="POST", description="HTTP method", pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers to include")
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters to include")
    body_template: Optional[str] = Field(None, description="Template for the request body")
    content_type: str = Field(default="application/json", description="Content type of the request", max_length=100)


class UpdateWebhookRequest(BaseModel):
    """Schema for updating an existing webhook"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://api.example.com/webhook/updated",
                "method": "PUT",
                "headers": {"Authorization": "Bearer new-token"},
                "query_params": {"key": "updated-value"},
                "body_template": '{"event": "updated", "data": "{{data}}"}',
                "content_type": "application/json",
                "job": {
                    "name": "Updated Job Name",
                    "schedule": "0 10 * * *",
                    "timezone": "America/New_York",
                    "enabled": True,
                },
            }
        }
    )

    url: Optional[str] = Field(None, description="URL to send the webhook to", min_length=1, max_length=1024)
    method: Optional[str] = Field(None, description="HTTP method", pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers to include")
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters to include")
    body_template: Optional[str] = Field(None, description="Template for the request body")
    content_type: Optional[str] = Field(None, description="Content type of the request", max_length=100)
    job: Optional[UpdateJobRequest] = Field(None, description="Job fields to update")


class CreateCronWebhookRequest(BaseModel):
    """Schema for creating a job with webhook via Cron integration"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job": {
                    "name": "Daily Report Job",
                    "schedule": "0 9 * * *",
                    "type": 1,
                    "timezone": "UTC",
                    "enabled": True,
                },
                "webhook": {
                    "url": "https://api.example.com/webhook",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer token123"},
                    "content_type": "application/json",
                },
            }
        }
    )

    job: CreateJobRequest = Field(..., description="Job configuration")
    webhook: CreateWebhookRequest = Field(..., description="Webhook configuration")
