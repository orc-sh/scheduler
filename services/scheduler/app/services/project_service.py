"""
Project service for managing CRUD operations on projects.
"""

import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.projects import Project

logger = logging.getLogger(__name__)


class ProjectService:
    """Service class for project-related operations"""

    def __init__(self, db: Session):
        """
        Initialize the project service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_project(self, user_id: str, name: str) -> Project:
        """
        Create a new project for a user.

        Args:
            user_id: ID of the user creating the project
            name: Name of the project

        Returns:
            Created Project instance
        """
        project = Project(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: str, user_id: str) -> Optional[Project]:
        """
        Get a specific project by ID for a user.

        Args:
            project_id: ID of the project to retrieve
            user_id: ID of the user (for authorization)

        Returns:
            Project instance if found and owned by user, None otherwise
        """
        return self.db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()

    def get_projects(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        Get all projects for a user with pagination.

        Args:
            user_id: ID of the user
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return

        Returns:
            List of Project instances
        """
        return self.db.query(Project).filter(Project.user_id == user_id).offset(skip).limit(limit).all()

    def get_projects_paginated(self, user_id: str, page: int = 1, page_size: int = 10) -> tuple[List[Project], dict]:
        """
        Get all projects for a user with page-based pagination and metadata.

        Args:
            user_id: ID of the user
            page: Page number (1-indexed)
            page_size: Number of records per page

        Returns:
            Tuple of (List of Project instances, pagination metadata dict)
        """
        # Ensure page is at least 1
        page = max(1, page)
        page_size = max(1, min(page_size, 100))  # Cap at 100 items per page

        # Get total count
        total_entries = self.count_projects(user_id)

        # Calculate total pages
        total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1

        # Ensure page doesn't exceed total pages
        page = min(page, total_pages)

        # Calculate offset
        skip = (page - 1) * page_size

        # Get projects for current page
        projects = self.db.query(Project).filter(Project.user_id == user_id).offset(skip).limit(page_size).all()

        # Build pagination metadata
        has_next = page < total_pages
        has_previous = page > 1

        pagination_metadata = {
            "current_page": page,
            "total_pages": total_pages,
            "total_entries": total_entries,
            "page_size": page_size,
            "has_next": has_next,
            "has_previous": has_previous,
            "next_page": page + 1 if has_next else None,
            "previous_page": page - 1 if has_previous else None,
        }

        return projects, pagination_metadata

    def update_project(self, project_id: str, user_id: str, name: str) -> Optional[Project]:
        """
        Update a project's name.

        Args:
            project_id: ID of the project to update
            user_id: ID of the user (for authorization)
            name: New name for the project

        Returns:
            Updated Project instance if found and owned by user, None otherwise
        """
        project = self.get_project(project_id, user_id)
        if not project:
            return None

        project.name = name  # type: ignore[assignment]
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """
        Delete a project.

        Args:
            project_id: ID of the project to delete
            user_id: ID of the user (for authorization)

        Returns:
            True if project was deleted, False if not found or not owned by user
        """
        project = self.get_project(project_id, user_id)
        if not project:
            return False

        self.db.delete(project)
        self.db.commit()
        return True

    def count_projects(self, user_id: str) -> int:
        """
        Count the total number of projects for a user.

        Args:
            user_id: ID of the user

        Returns:
            Total count of projects
        """
        return self.db.query(Project).filter(Project.user_id == user_id).count()

    def get_or_create_project_by_name(
        self, user_id: str, project_name: str, user=None, default_plan_id: str = "free"
    ) -> Project:
        """
        Get an existing project by name or create it if it doesn't exist.
        Automatically creates a subscription for new projects.

        Args:
            user_id: ID of the user
            project_name: Name of the project to find or create
            user: User instance (optional, needed for subscription creation)
            default_plan_id: Default plan ID for new subscriptions (default: "free")

        Returns:
            Project instance (either existing or newly created)
        """
        # Try to find existing project
        project = self.db.query(Project).filter(Project.user_id == user_id, Project.name == project_name).first()

        # If not found, create new project
        if not project:
            project = self.create_project(user_id, project_name)

            # Automatically create subscription for new project
            if user:
                try:
                    from app.services.subscription_service import get_subscription_service

                    subscription_service = get_subscription_service(self.db)

                    # Get user email for subscription
                    customer_email = user.email or f"{user_id}@example.com"
                    customer_first_name = None
                    customer_last_name = None

                    # Try to extract name from user metadata
                    if user.user_metadata:
                        if "name" in user.user_metadata:
                            name_parts = user.user_metadata["name"].split(" ", 1)
                            customer_first_name = name_parts[0] if len(name_parts) > 0 else None
                            customer_last_name = name_parts[1] if len(name_parts) > 1 else None
                        elif "full_name" in user.user_metadata:
                            name_parts = user.user_metadata["full_name"].split(" ", 1)
                            customer_first_name = name_parts[0] if len(name_parts) > 0 else None
                            customer_last_name = name_parts[1] if len(name_parts) > 1 else None

                    # Create subscription with default plan
                    subscription_service.create_subscription(
                        project_id=str(project.id),
                        plan_id=default_plan_id,
                        customer_email=customer_email,
                        customer_first_name=customer_first_name,
                        customer_last_name=customer_last_name,
                    )
                    logger.info(f"Created subscription for project {project.id} with plan {default_plan_id}")
                except Exception as e:
                    # Log error but don't fail project creation
                    logger.error(f"Failed to create subscription for project {project.id}: {str(e)}")

        return project


def get_project_service(db: Session) -> ProjectService:
    """
    Factory function to create a ProjectService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        ProjectService instance
    """
    return ProjectService(db)
