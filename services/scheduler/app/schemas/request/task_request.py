from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from app.models.http_method import HttpMethod

class WebhookRequest(BaseModel):
    url: str  # Webhook URL to trigger
    method: HttpMethod  # HTTP method
    headers: Optional[Dict[str, str]] = None  # Optional headers for the webhook request
    body: Optional[Dict[str, str]] = None  # JSON data as a string

class TaskRequest(BaseModel): 
    name: str  # Unique job identifier
    scheduled_time: datetime  # Scheduled time in ISO 8601 format
    cron: Optional[str] = None  # Cron expression (e.g., "*/5 * * * *")
    timezone: Optional[str] = "UTC"  # Optional timezone, defaults to UTC
    webhook: WebhookRequest  # Webhook to be triggered
    active: Optional[bool] = True # Optional active status

    class Config:
        # Enabling the use of datetime.isoformat() when serializing datetime fields
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
