from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectResponse(BaseModel):
    """Response schema for project data"""

    model_config = ConfigDict(from_attributes=True)  # Enables ORM mode for SQLAlchemy models

    id: str = Field(..., description="Project unique identifier")
    user_id: str = Field(..., description="User ID who owns the project")
    name: str = Field(..., description="Project name")
    created_at: Optional[datetime] = Field(None, description="Project creation timestamp")
