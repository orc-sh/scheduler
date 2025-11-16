# Request schemas for scheduler service
# Add scheduler-specific request schemas here (e.g., CreateJobRequest, UpdateWebhookRequest, etc.)

from .project_schemas import CreateProjectRequest, UpdateProjectRequest

__all__ = ["CreateProjectRequest", "UpdateProjectRequest"]
