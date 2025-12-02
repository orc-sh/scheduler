"""
Response schemas for URL operations.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.response.account_schemas import AccountResponse


class UrlResponse(BaseModel):
    """Schema for URL response"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "account_id": "123e4567-e89b-12d3-a456-426614174001",
                "unique_identifier": "abc123xyz",
                "path": "/webhooks/abc123xyz",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
        },
    )

    id: str = Field(..., description="URL ID")
    account_id: str = Field(..., description="Account ID this URL belongs to")
    unique_identifier: str = Field(..., description="Unique identifier for the URL")
    path: str = Field(..., description="Full path to access this URL")
    created_at: datetime = Field(..., description="When the URL was created")
    updated_at: datetime = Field(..., description="When the URL was last updated")
    account: Optional[AccountResponse] = Field(None, description="Associated account information")


class UrlLogResponse(BaseModel):
    """Schema for URL log response"""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "url_id": "123e4567-e89b-12d3-a456-426614174002",
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "query_params": {"key": "value"},
                "body": '{"data": "test"}',
                "response_status": 200,
                "response_headers": {"Content-Type": "application/json"},
                "response_body": '{"success": true}',
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "created_at": "2024-01-01T00:00:00",
            }
        },
    )

    id: str = Field(..., description="URL log ID")
    url_id: str = Field(..., description="URL ID this log belongs to")
    method: str = Field(..., description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="Request headers")
    query_params: Optional[Dict[str, str]] = Field(None, description="Query parameters")
    body: Optional[str] = Field(None, description="Request body")
    response_status: Optional[int] = Field(None, description="Response status code")
    response_headers: Optional[Dict[str, str]] = Field(None, description="Response headers")
    response_body: Optional[str] = Field(None, description="Response body")
    ip_address: Optional[str] = Field(None, description="IP address of the requester")
    user_agent: Optional[str] = Field(None, description="User agent of the requester")
    created_at: datetime = Field(..., description="When the request was received")


class UrlWithLogsResponse(BaseModel):
    """Schema for URL response with logs"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "account_id": "123e4567-e89b-12d3-a456-426614174001",
                "unique_identifier": "abc123xyz",
                "path": "/webhooks/abc123xyz",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "logs": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174003",
                        "method": "POST",
                        "headers": {"Content-Type": "application/json"},
                        "body": '{"data": "test"}',
                        "created_at": "2024-01-01T00:00:00",
                    }
                ],
            }
        },
    )

    id: str = Field(..., description="URL ID")
    account_id: str = Field(..., description="Account ID this URL belongs to")
    unique_identifier: str = Field(..., description="Unique identifier for the URL")
    path: str = Field(..., description="Full path to access this URL")
    created_at: datetime = Field(..., description="When the URL was created")
    updated_at: datetime = Field(..., description="When the URL was last updated")
    logs: List[UrlLogResponse] = Field(default_factory=list, description="List of URL logs")
