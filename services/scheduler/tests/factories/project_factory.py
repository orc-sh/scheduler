"""
Project-specific test data factories and helpers.
"""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.models.projects import Project


class ProjectFactory:
    """Factory for creating Project test objects."""

    @staticmethod
    def create(
        db: Session,
        user_id: str,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Project:
        """
        Create a project in the database.
        """
        project = Project(
            id=project_id or str(uuid.uuid4()),
            user_id=user_id,
            name=name or f"Test Project {uuid.uuid4().hex[:8]}",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def create_batch(
        db: Session,
        user_id: str,
        count: int = 5,
        name_prefix: Optional[str] = None,
    ) -> list[Project]:
        """
        Create multiple projects in the database.
        """
        projects: list[Project] = []
        for i in range(count):
            name = f"{name_prefix} {i + 1}" if name_prefix else f"Test Project {i + 1}"
            project = ProjectFactory.create(db=db, user_id=user_id, name=name)
            projects.append(project)
        return projects

    @staticmethod
    def build(
        user_id: str,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Project:
        """
        Build a project object without saving to database.
        """
        return Project(
            id=project_id or str(uuid.uuid4()),
            user_id=user_id,
            name=name or f"Test Project {uuid.uuid4().hex[:8]}",
        )


def create_test_project_data(count: int = 1) -> list[dict]:
    """
    Create raw project data dictionaries (not model instances).
    """
    return [
        {
            "name": f"Test Project {i + 1}",
        }
        for i in range(count)
    ]


def create_project_update_data(name: Optional[str] = None) -> dict:
    """
    Create project update data dictionary.
    """
    return {"name": name or f"Updated Project {uuid.uuid4().hex[:8]}"}
