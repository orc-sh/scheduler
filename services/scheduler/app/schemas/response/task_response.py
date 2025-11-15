from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator

class WebhookResponse(BaseModel):
    url: str
    method: str
    headers: Optional[Dict[str, str]]
    body: Optional[Dict[str, str]]

    class Config:
        validate_assignment = True

    @field_validator('headers')
    def set_headers(cls, headers):
        return headers or {}
    
    @field_validator('body')
    def set_body(cls, body):
        return body or {}

class TaskResponse(BaseModel):
    id: int
    name: str
    scheduled_time: datetime
    webhook: Optional[WebhookResponse]
    cron: Optional[str]
    active: bool
