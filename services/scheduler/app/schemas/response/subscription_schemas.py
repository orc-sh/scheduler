"""
Response schemas for subscription operations.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sub_1234567890",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "chargebee_subscription_id": "sub_1234567890",
                "chargebee_customer_id": "cust_1234567890",
                "plan_id": "pro-plan",
                "status": "active",
                "current_term_start": "2024-01-01T00:00:00Z",
                "current_term_end": "2024-02-01T00:00:00Z",
                "trial_end": None,
                "cancelled_at": None,
                "cancel_reason": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        }
    )

    id: str = Field(..., description="Subscription ID")
    project_id: str = Field(..., description="Associated project ID")
    chargebee_subscription_id: str = Field(..., description="Chargebee subscription ID")
    chargebee_customer_id: str = Field(..., description="Chargebee customer ID")
    plan_id: str = Field(..., description="Chargebee plan ID")
    status: str = Field(..., description="Subscription status (active, cancelled, etc.)")
    current_term_start: Optional[datetime] = Field(None, description="Current term start date")
    current_term_end: Optional[datetime] = Field(None, description="Current term end date")
    trial_end: Optional[datetime] = Field(None, description="Trial end date")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation date")
    cancel_reason: Optional[str] = Field(None, description="Cancellation reason")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_model(cls, subscription) -> "SubscriptionResponse":
        """
        Create SubscriptionResponse from Subscription model.

        Args:
            subscription: Subscription model instance

        Returns:
            SubscriptionResponse instance
        """
        return cls(
            id=str(subscription.id),
            project_id=str(subscription.project_id),
            chargebee_subscription_id=subscription.chargebee_subscription_id,
            chargebee_customer_id=subscription.chargebee_customer_id,
            plan_id=subscription.plan_id,
            status=subscription.status,
            current_term_start=subscription.current_term_start,
            current_term_end=subscription.current_term_end,
            trial_end=subscription.trial_end,
            cancelled_at=subscription.cancelled_at,
            cancel_reason=subscription.cancel_reason,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
        )
