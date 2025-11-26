"""
Request schemas for load test operations.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateCollectionRequest(BaseModel):
    """Schema for creating a new webhook collection"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "API Collection",
                "description": "Collection of API endpoints for testing",
            }
        }
    )

    project_id: Optional[str] = Field(
        None, description="Project ID (optional, will use user's first project if not provided)", min_length=1
    )
    name: Optional[str] = Field(None, description="Name of the collection (can be blank)", max_length=255)
    description: Optional[str] = Field(None, description="Description of the collection")


class UpdateCollectionRequest(BaseModel):
    """Schema for updating an existing webhook collection"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Updated API Collection",
                "description": "Updated description",
            }
        }
    )

    name: Optional[str] = Field(None, description="Name of the collection", max_length=255)
    description: Optional[str] = Field(None, description="Description of the collection")


class CreateLoadTestRunRequest(BaseModel):
    """Schema for creating a new load test run from a collection"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "collection_id": "123e4567-e89b-12d3-a456-426614174000",
                "concurrent_users": 50,
                "duration_seconds": 120,
                "requests_per_second": 100,
            }
        }
    )

    collection_id: str = Field(..., description="ID of the webhook collection")
    concurrent_users: int = Field(10, description="Number of concurrent users", ge=1, le=1000)
    duration_seconds: int = Field(60, description="Duration of test in seconds", ge=1, le=3600)
    requests_per_second: Optional[int] = Field(None, description="Optional rate limit (requests per second)", ge=1)


class CreateLoadTestReportRequest(BaseModel):
    """Schema for creating a new load test report"""

    run_id: str = Field(..., description="ID of the load test run")
    name: Optional[str] = Field(None, description="Optional report name", max_length=255)
    notes: Optional[str] = Field(None, description="Optional notes about the report")


class CreateWebhookRequest(BaseModel):
    """Schema for creating a new webhook for a collection"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://api.example.com/api/users",
                "method": "GET",
                "headers": {"Authorization": "Bearer token"},
                "order": 0,
            }
        }
    )

    url: str = Field(..., description="Full endpoint URL to test", min_length=1, max_length=2048)
    method: str = Field(..., description="HTTP method", max_length=10)
    headers: Optional[Dict[str, Any]] = Field(None, description="Request headers")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    body_template: Optional[str] = Field(None, description="Request body template")
    content_type: Optional[str] = Field(None, description="Content type (default: application/json)", max_length=100)
    order: Optional[int] = Field(None, description="Execution order (lower numbers execute first)")


class UpdateWebhookRequest(BaseModel):
    """Schema for updating an existing webhook"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://api.example.com/api/users",
                "method": "POST",
                "order": 1,
            }
        }
    )

    url: Optional[str] = Field(None, description="Full endpoint URL to test", min_length=1, max_length=2048)
    method: Optional[str] = Field(None, description="HTTP method", max_length=10)
    headers: Optional[Dict[str, Any]] = Field(None, description="Request headers")
    query_params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    body_template: Optional[str] = Field(None, description="Request body template")
    content_type: Optional[str] = Field(None, description="Content type", max_length=100)
    order: Optional[int] = Field(None, description="Execution order (lower numbers execute first)")


class ReorderWebhooksRequest(BaseModel):
    """Schema for reordering webhooks in a collection"""

    webhook_ids: List[str] = Field(..., description="List of webhook IDs in desired order")
