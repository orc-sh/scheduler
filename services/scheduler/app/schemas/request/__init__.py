# Request schemas for scheduler service
# Add scheduler-specific request schemas here (e.g., CreateJobRequest, UpdateWebhookRequest, etc.)

from .project_schemas import CreateProjectRequest, UpdateProjectRequest
from .subscription_schemas import CancelSubscriptionRequest, UpdateSubscriptionRequest

__all__ = [
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "UpdateSubscriptionRequest",
    "CancelSubscriptionRequest",
]
