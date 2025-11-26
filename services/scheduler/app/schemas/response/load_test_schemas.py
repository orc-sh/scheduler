"""
Response schemas for load test operations.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WebhookResponse(BaseModel):
    """Schema for webhook information"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    method: str
    headers: Optional[dict] = None
    query_params: Optional[dict] = None
    body_template: Optional[str] = None
    content_type: Optional[str] = None
    order: Optional[int] = None


class LoadTestResultResponse(BaseModel):
    """Schema for individual load test result"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    load_test_report_id: str
    endpoint_path: str
    method: str
    request_headers: Optional[dict] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_headers: Optional[dict] = None
    response_body: Optional[str] = None
    response_time_ms: int
    error_message: Optional[str] = None
    is_success: bool
    created_at: datetime


class LoadTestReportResponse(BaseModel):
    """Schema for load test report"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    load_test_run_id: str
    name: Optional[str] = None
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: Optional[int] = None
    min_response_time_ms: Optional[int] = None
    max_response_time_ms: Optional[int] = None
    p95_response_time_ms: Optional[int] = None
    p99_response_time_ms: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LoadTestReportWithResultsResponse(BaseModel):
    """Schema for load test report with results"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    load_test_run_id: str
    name: Optional[str] = None
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: Optional[int] = None
    min_response_time_ms: Optional[int] = None
    max_response_time_ms: Optional[int] = None
    p95_response_time_ms: Optional[int] = None
    p99_response_time_ms: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    results: List[LoadTestResultResponse] = Field(default_factory=list)


class CollectionResponse(BaseModel):
    """Schema for webhook collection"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str] = None  # Optional for nested responses
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None  # Optional for nested responses
    updated_at: Optional[datetime] = None  # Optional for nested responses
    # Nested webhooks info (optional for nested responses)
    webhooks: List[WebhookResponse] = Field(default_factory=list)


class LoadTestRunResponse(BaseModel):
    """Schema for load test run"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_id: str
    status: str
    concurrent_users: int
    duration_seconds: int
    requests_per_second: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    collection: Optional[CollectionResponse] = None


class LoadTestRunWithReportsResponse(BaseModel):
    """Schema for load test run with reports"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    collection_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    reports: List[LoadTestReportWithResultsResponse] = Field(default_factory=list)
    collection: Optional[CollectionResponse] = None


class CollectionWithRunsResponse(BaseModel):
    """Schema for webhook collection with runs"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    webhooks: List[WebhookResponse] = Field(default_factory=list)
    runs: List[LoadTestRunResponse] = Field(default_factory=list)
