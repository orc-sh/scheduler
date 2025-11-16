# Schemas for scheduler service
# Authentication schemas are in the auth service
# Add scheduler-specific schemas here (jobs, webhooks, projects, etc.)

from .request import CreateProjectRequest, UpdateProjectRequest
from .response import PaginatedResponse, PaginationMetadata, ProjectResponse

__all__ = [
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "PaginatedResponse",
    "PaginationMetadata",
    "ProjectResponse",
]
