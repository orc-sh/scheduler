"""
Unit tests for ProjectService.

These tests verify the service layer logic for project CRUD operations
without making actual API requests.
"""

import pytest
from sqlalchemy.orm import Session

from app.services.project_service import ProjectService, get_project_service
from tests.factories import ProjectFactory


@pytest.mark.unit
class TestProjectServiceCreate:
    """Tests for project creation."""

    def test_create_project_success(self, db_session: Session, test_user):
        """Test creating a project successfully."""
        service = ProjectService(db_session)

        project = service.create_project(user_id=test_user.id, name="My New Project")

        assert project.id is not None
        assert project.user_id == test_user.id
        assert project.name == "My New Project"
        assert project.created_at is not None

    def test_create_project_generates_uuid(self, db_session: Session, test_user):
        """Test that project ID is auto-generated as UUID."""
        service = ProjectService(db_session)

        project = service.create_project(user_id=test_user.id, name="Test Project")

        # Check UUID format
        assert len(project.id) == 36  # UUID format: 8-4-4-4-12
        assert project.id.count("-") == 4

    def test_create_multiple_projects(self, db_session: Session, test_user):
        """Test creating multiple projects for the same user."""
        service = ProjectService(db_session)

        project1 = service.create_project(test_user.id, "Project 1")
        project2 = service.create_project(test_user.id, "Project 2")

        assert project1.id != project2.id
        assert project1.name != project2.name
        assert project1.user_id == project2.user_id


@pytest.mark.unit
class TestProjectServiceGet:
    """Tests for retrieving projects."""

    def test_get_project_by_id_success(self, db_session: Session, test_user):
        """Test retrieving a specific project by ID."""
        # Create a project
        created_project = ProjectFactory.create(db_session, test_user.id, "Test Project")

        # Retrieve it
        service = ProjectService(db_session)
        project = service.get_project(created_project.id, test_user.id)

        assert project is not None
        assert project.id == created_project.id
        assert project.name == "Test Project"

    def test_get_project_not_found(self, db_session: Session, test_user):
        """Test retrieving a non-existent project returns None."""
        service = ProjectService(db_session)

        project = service.get_project("non-existent-id", test_user.id)

        assert project is None

    def test_get_project_wrong_user(self, db_session: Session, test_user, another_user):
        """Test that users can't access other users' projects."""
        # Create project for test_user
        created_project = ProjectFactory.create(db_session, test_user.id, "Test Project")

        # Try to access with another_user
        service = ProjectService(db_session)
        project = service.get_project(created_project.id, another_user.id)

        assert project is None

    def test_get_projects_empty_list(self, db_session: Session, test_user):
        """Test retrieving projects when user has none."""
        service = ProjectService(db_session)

        projects = service.get_projects(test_user.id)

        assert projects == []

    def test_get_projects_returns_all_user_projects(self, db_session: Session, test_user):
        """Test retrieving all projects for a user."""
        # Create multiple projects
        ProjectFactory.create_batch(db_session, test_user.id, count=3, name_prefix="Project")

        service = ProjectService(db_session)
        projects = service.get_projects(test_user.id)

        assert len(projects) == 3
        assert all(p.user_id == test_user.id for p in projects)

    def test_get_projects_filters_by_user(self, db_session: Session, test_user, another_user):
        """Test that get_projects only returns the specified user's projects."""
        # Create projects for different users
        ProjectFactory.create_batch(db_session, test_user.id, count=2)
        ProjectFactory.create_batch(db_session, another_user.id, count=3)

        service = ProjectService(db_session)
        projects = service.get_projects(test_user.id)

        assert len(projects) == 2
        assert all(p.user_id == test_user.id for p in projects)

    def test_get_projects_with_pagination(self, db_session: Session, test_user):
        """Test retrieving projects with skip and limit."""
        # Create 10 projects
        ProjectFactory.create_batch(db_session, test_user.id, count=10)

        service = ProjectService(db_session)

        # Get first 5
        projects_page1 = service.get_projects(test_user.id, skip=0, limit=5)
        assert len(projects_page1) == 5

        # Get next 5
        projects_page2 = service.get_projects(test_user.id, skip=5, limit=5)
        assert len(projects_page2) == 5

        # Ensure they're different projects
        page1_ids = {p.id for p in projects_page1}
        page2_ids = {p.id for p in projects_page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.unit
class TestProjectServiceGetPaginated:
    """Tests for paginated project retrieval."""

    def test_get_projects_paginated_first_page(self, db_session: Session, test_user):
        """Test getting first page of projects."""
        # Create 25 projects
        ProjectFactory.create_batch(db_session, test_user.id, count=25)

        service = ProjectService(db_session)
        projects, metadata = service.get_projects_paginated(test_user.id, page=1, page_size=10)

        assert len(projects) == 10
        assert metadata["current_page"] == 1
        assert metadata["total_pages"] == 3
        assert metadata["total_entries"] == 25
        assert metadata["page_size"] == 10
        assert metadata["has_next"] is True
        assert metadata["has_previous"] is False
        assert metadata["next_page"] == 2
        assert metadata["previous_page"] is None

    def test_get_projects_paginated_middle_page(self, db_session: Session, test_user):
        """Test getting middle page of projects."""
        ProjectFactory.create_batch(db_session, test_user.id, count=25)

        service = ProjectService(db_session)
        projects, metadata = service.get_projects_paginated(test_user.id, page=2, page_size=10)

        assert len(projects) == 10
        assert metadata["current_page"] == 2
        assert metadata["has_next"] is True
        assert metadata["has_previous"] is True
        assert metadata["next_page"] == 3
        assert metadata["previous_page"] == 1

    def test_get_projects_paginated_last_page(self, db_session: Session, test_user):
        """Test getting last page of projects."""
        ProjectFactory.create_batch(db_session, test_user.id, count=25)

        service = ProjectService(db_session)
        projects, metadata = service.get_projects_paginated(test_user.id, page=3, page_size=10)

        assert len(projects) == 5  # Only 5 items on last page
        assert metadata["current_page"] == 3
        assert metadata["has_next"] is False
        assert metadata["has_previous"] is True
        assert metadata["next_page"] is None
        assert metadata["previous_page"] == 2

    def test_get_projects_paginated_empty_results(self, db_session: Session, test_user):
        """Test pagination with no projects."""
        service = ProjectService(db_session)
        projects, metadata = service.get_projects_paginated(test_user.id, page=1, page_size=10)

        assert len(projects) == 0
        assert metadata["total_entries"] == 0
        assert metadata["total_pages"] == 1
        assert metadata["current_page"] == 1
        assert metadata["has_next"] is False
        assert metadata["has_previous"] is False

    def test_get_projects_paginated_page_exceeds_total(self, db_session: Session, test_user):
        """Test requesting page beyond available pages."""
        ProjectFactory.create_batch(db_session, test_user.id, count=5)

        service = ProjectService(db_session)
        projects, metadata = service.get_projects_paginated(test_user.id, page=10, page_size=10)

        # Should return last valid page
        assert metadata["current_page"] == 1
        assert len(projects) == 5

    def test_get_projects_paginated_caps_page_size(self, db_session: Session, test_user):
        """Test that page_size is capped at 100."""
        ProjectFactory.create_batch(db_session, test_user.id, count=150)

        service = ProjectService(db_session)
        projects, metadata = service.get_projects_paginated(test_user.id, page=1, page_size=200)

        assert metadata["page_size"] == 100
        assert len(projects) == 100


@pytest.mark.unit
class TestProjectServiceUpdate:
    """Tests for project updates."""

    def test_update_project_success(self, db_session: Session, test_user):
        """Test updating a project successfully."""
        # Create project
        created_project = ProjectFactory.create(db_session, test_user.id, "Original Name")

        # Update it
        service = ProjectService(db_session)
        updated_project = service.update_project(created_project.id, test_user.id, "Updated Name")

        assert updated_project is not None
        assert updated_project.id == created_project.id
        assert updated_project.name == "Updated Name"

    def test_update_project_not_found(self, db_session: Session, test_user):
        """Test updating a non-existent project returns None."""
        service = ProjectService(db_session)

        result = service.update_project("non-existent-id", test_user.id, "New Name")

        assert result is None

    def test_update_project_wrong_user(self, db_session: Session, test_user, another_user):
        """Test that users can't update other users' projects."""
        # Create project for test_user
        created_project = ProjectFactory.create(db_session, test_user.id, "Original Name")

        # Try to update with another_user
        service = ProjectService(db_session)
        result = service.update_project(created_project.id, another_user.id, "Hacked Name")

        assert result is None

        # Verify original project unchanged
        db_session.refresh(created_project)
        assert created_project.name == "Original Name"


@pytest.mark.unit
class TestProjectServiceDelete:
    """Tests for project deletion."""

    def test_delete_project_success(self, db_session: Session, test_user):
        """Test deleting a project successfully."""
        # Create project
        created_project = ProjectFactory.create(db_session, test_user.id, "To Delete")
        project_id = created_project.id

        # Delete it
        service = ProjectService(db_session)
        result = service.delete_project(project_id, test_user.id)

        assert result is True

        # Verify it's gone
        deleted_project = service.get_project(project_id, test_user.id)
        assert deleted_project is None

    def test_delete_project_not_found(self, db_session: Session, test_user):
        """Test deleting a non-existent project returns False."""
        service = ProjectService(db_session)

        result = service.delete_project("non-existent-id", test_user.id)

        assert result is False

    def test_delete_project_wrong_user(self, db_session: Session, test_user, another_user):
        """Test that users can't delete other users' projects."""
        # Create project for test_user
        created_project = ProjectFactory.create(db_session, test_user.id, "Protected")
        project_id = created_project.id

        # Try to delete with another_user
        service = ProjectService(db_session)
        result = service.delete_project(project_id, another_user.id)

        assert result is False

        # Verify project still exists
        project = service.get_project(project_id, test_user.id)
        assert project is not None


@pytest.mark.unit
class TestProjectServiceCount:
    """Tests for counting projects."""

    def test_count_projects_zero(self, db_session: Session, test_user):
        """Test counting when user has no projects."""
        service = ProjectService(db_session)

        count = service.count_projects(test_user.id)

        assert count == 0

    def test_count_projects_multiple(self, db_session: Session, test_user):
        """Test counting multiple projects."""
        ProjectFactory.create_batch(db_session, test_user.id, count=7)

        service = ProjectService(db_session)
        count = service.count_projects(test_user.id)

        assert count == 7

    def test_count_projects_filters_by_user(self, db_session: Session, test_user, another_user):
        """Test that count only includes the specified user's projects."""
        ProjectFactory.create_batch(db_session, test_user.id, count=3)
        ProjectFactory.create_batch(db_session, another_user.id, count=5)

        service = ProjectService(db_session)
        count = service.count_projects(test_user.id)

        assert count == 3


@pytest.mark.unit
class TestProjectServiceFactory:
    """Tests for the service factory function."""

    def test_get_project_service_returns_instance(self, db_session: Session):
        """Test that factory function returns ProjectService instance."""
        service = get_project_service(db_session)

        assert isinstance(service, ProjectService)
        assert service.db == db_session

    def test_get_project_service_creates_new_instances(self, db_session: Session):
        """Test that factory creates new instances each time."""
        service1 = get_project_service(db_session)
        service2 = get_project_service(db_session)

        # Should be different instances
        assert service1 is not service2
        # But should share the same db session
        assert service1.db is service2.db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
