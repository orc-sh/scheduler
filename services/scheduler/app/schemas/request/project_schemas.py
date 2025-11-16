from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    """Request schema for creating a new project"""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")


class UpdateProjectRequest(BaseModel):
    """Request schema for updating an existing project"""

    name: str = Field(..., min_length=1, max_length=255, description="Updated project name")
