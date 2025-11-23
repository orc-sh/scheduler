"""
Request schemas for subscription operations.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UpdateSubscriptionRequest(BaseModel):
    """Schema for updating a subscription (upgrade/downgrade plan)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "plan_id": "enterprise-plan",
            }
        }
    )

    plan_id: str = Field(..., description="New Chargebee plan ID")


class CancelSubscriptionRequest(BaseModel):
    """Schema for cancelling a subscription"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cancel_reason": "No longer needed",
            }
        }
    )

    cancel_reason: Optional[str] = Field(None, description="Reason for cancellation")
