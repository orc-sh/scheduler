"""
Integration tests for Projects API endpoints.

These tests verify the complete API functionality including
request/response handling, authentication, and database interactions.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.context.user_context import set_current_user_context
from app.models.user import User
from tests.factories import ProjectFactory


@pytest.mark.integration
class TestCreateProjectAPI:
    """Tests for POST /projects endpoint."""

    def test_create_project_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test creating a project successfully."""
        set_current_user_context(test_user)

        response = client.post(
            "/projects",
            json={"name": "My Test Project"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Test Project"
        assert data["user_id"] == test_user.id
        assert "id" in data
        assert "created_at" in data

    def test_create_project_without_auth(self, client: TestClient):
        """Test creating a project without authentication fails."""
        response = client.post(
            "/projects",
            json={"name": "Test Project"},
        )

        assert response.status_code == 401

    def test_create_project_empty_name(self, client: TestClient, test_user: User):
        """Test creating a project with empty name fails validation."""
        set_current_user_context(test_user)

        response = client.post(
            "/projects",
            json={"name": ""},
        )

        assert response.status_code == 422

    def test_create_project_missing_name(self, client: TestClient, test_user: User):
        """Test creating a project without name field fails."""
        set_current_user_context(test_user)

        response = client.post(
            "/projects",
            json={},
        )

        assert response.status_code == 422

    def test_create_project_name_too_long(self, client: TestClient, test_user: User):
        """Test creating a project with name exceeding max length."""
        set_current_user_context(test_user)

        response = client.post(
            "/projects",
            json={"name": "x" * 256},  # Max is 255
        )

        assert response.status_code == 422

    def test_create_multiple_projects_different_users(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that different users can create projects with the same name."""
        # User 1 creates project
        set_current_user_context(test_user)
        response1 = client.post("/projects", json={"name": "Shared Name"})
        assert response1.status_code == 201

        # User 2 creates project with same name
        set_current_user_context(another_user)
        response2 = client.post("/projects", json={"name": "Shared Name"})
        assert response2.status_code == 201

        # Should be different projects
        assert response1.json()["id"] != response2.json()["id"]
        assert response1.json()["user_id"] != response2.json()["user_id"]


@pytest.mark.integration
class TestGetProjectsAPI:
    """Tests for GET /projects endpoint (list all projects)."""

    def test_get_projects_empty_list(self, client: TestClient, test_user: User):
        """Test getting projects when user has none."""
        set_current_user_context(test_user)

        response = client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total_entries"] == 0
        assert data["pagination"]["total_pages"] == 1

    def test_get_projects_with_data(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting projects with pagination."""
        # Create projects
        ProjectFactory.create_batch(db_session, test_user.id, count=5)
        set_current_user_context(test_user)

        response = client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["total_entries"] == 5
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["has_next"] is False

    def test_get_projects_pagination_first_page(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting first page of projects."""
        # Create 25 projects
        ProjectFactory.create_batch(db_session, test_user.id, count=25)
        set_current_user_context(test_user)

        response = client.get("/projects?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["current_page"] == 1
        assert data["pagination"]["total_pages"] == 3
        assert data["pagination"]["total_entries"] == 25
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is False
        assert data["pagination"]["next_page"] == 2
        assert data["pagination"]["previous_page"] is None

    def test_get_projects_pagination_middle_page(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting middle page of projects."""
        ProjectFactory.create_batch(db_session, test_user.id, count=25)
        set_current_user_context(test_user)

        response = client.get("/projects?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["pagination"]["current_page"] == 2
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_previous"] is True
        assert data["pagination"]["next_page"] == 3
        assert data["pagination"]["previous_page"] == 1

    def test_get_projects_pagination_last_page(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting last page of projects."""
        ProjectFactory.create_batch(db_session, test_user.id, count=25)
        set_current_user_context(test_user)

        response = client.get("/projects?page=3&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["current_page"] == 3
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["next_page"] is None

    def test_get_projects_custom_page_size(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting projects with custom page size."""
        ProjectFactory.create_batch(db_session, test_user.id, count=20)
        set_current_user_context(test_user)

        response = client.get("/projects?page=1&page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["page_size"] == 5
        assert data["pagination"]["total_pages"] == 4

    def test_get_projects_filters_by_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users only see their own projects."""
        # Create projects for different users
        ProjectFactory.create_batch(db_session, test_user.id, count=3)
        ProjectFactory.create_batch(db_session, another_user.id, count=5)

        set_current_user_context(test_user)
        response = client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert all(p["user_id"] == test_user.id for p in data["data"])

    def test_get_projects_without_auth(self, client: TestClient):
        """Test getting projects without authentication fails."""
        response = client.get("/projects")

        assert response.status_code == 401

    def test_get_projects_invalid_page_number(self, client: TestClient, test_user: User):
        """Test that invalid page numbers are handled."""
        set_current_user_context(test_user)

        response = client.get("/projects?page=0")

        # Should use minimum page of 1
        assert response.status_code == 422  # Validation error

    def test_get_projects_page_size_too_large(self, client: TestClient, db_session: Session, test_user: User):
        """Test that page_size is capped at maximum."""
        ProjectFactory.create_batch(db_session, test_user.id, count=150)
        set_current_user_context(test_user)

        response = client.get("/projects?page=1&page_size=200")

        # Should be capped at 100
        assert response.status_code == 422  # Validation error for exceeding max


@pytest.mark.integration
class TestGetProjectAPI:
    """Tests for GET /projects/{project_id} endpoint."""

    def test_get_project_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting a specific project by ID."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        set_current_user_context(test_user)

        response = client.get(f"/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Test Project"
        assert data["user_id"] == test_user.id

    def test_get_project_not_found(self, client: TestClient, test_user: User):
        """Test getting a non-existent project returns 404."""
        set_current_user_context(test_user)

        response = client.get("/projects/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_project_wrong_user(self, client: TestClient, db_session: Session, test_user: User, another_user: User):
        """Test that users can't access other users' projects."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")
        set_current_user_context(another_user)

        response = client.get(f"/projects/{project.id}")

        assert response.status_code == 404

    def test_get_project_without_auth(self, client: TestClient, db_session: Session, test_user: User):
        """Test getting a project without authentication fails."""
        project = ProjectFactory.create(db_session, test_user.id, "Test Project")

        response = client.get(f"/projects/{project.id}")

        assert response.status_code == 401


@pytest.mark.integration
class TestUpdateProjectAPI:
    """Tests for PUT /projects/{project_id} endpoint."""

    def test_update_project_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating a project successfully."""
        project = ProjectFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(test_user)

        response = client.put(
            f"/projects/{project.id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["name"] == "Updated Name"
        assert data["user_id"] == test_user.id

    def test_update_project_not_found(self, client: TestClient, test_user: User):
        """Test updating a non-existent project returns 404."""
        set_current_user_context(test_user)

        response = client.put(
            "/projects/non-existent-id",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    def test_update_project_wrong_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users can't update other users' projects."""
        project = ProjectFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(another_user)

        response = client.put(
            f"/projects/{project.id}",
            json={"name": "Hacked Name"},
        )

        assert response.status_code == 404

        # Verify project unchanged
        db_session.refresh(project)
        assert project.name == "Original Name"

    def test_update_project_empty_name(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating with empty name fails validation."""
        project = ProjectFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(test_user)

        response = client.put(
            f"/projects/{project.id}",
            json={"name": ""},
        )

        assert response.status_code == 422

    def test_update_project_missing_name(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating without name field fails."""
        project = ProjectFactory.create(db_session, test_user.id, "Original Name")
        set_current_user_context(test_user)

        response = client.put(
            f"/projects/{project.id}",
            json={},
        )

        assert response.status_code == 422

    def test_update_project_without_auth(self, client: TestClient, db_session: Session, test_user: User):
        """Test updating a project without authentication fails."""
        project = ProjectFactory.create(db_session, test_user.id, "Original Name")

        response = client.put(
            f"/projects/{project.id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 401


@pytest.mark.integration
class TestDeleteProjectAPI:
    """Tests for DELETE /projects/{project_id} endpoint."""

    def test_delete_project_success(self, client: TestClient, db_session: Session, test_user: User):
        """Test deleting a project successfully."""
        project = ProjectFactory.create(db_session, test_user.id, "To Delete")
        project_id = project.id
        set_current_user_context(test_user)

        response = client.delete(f"/projects/{project_id}")

        assert response.status_code == 204
        assert response.content == b""

        # Verify project is deleted
        verify_response = client.get(f"/projects/{project_id}")
        assert verify_response.status_code == 404

    def test_delete_project_not_found(self, client: TestClient, test_user: User):
        """Test deleting a non-existent project returns 404."""
        set_current_user_context(test_user)

        response = client.delete("/projects/non-existent-id")

        assert response.status_code == 404

    def test_delete_project_wrong_user(
        self, client: TestClient, db_session: Session, test_user: User, another_user: User
    ):
        """Test that users can't delete other users' projects."""
        project = ProjectFactory.create(db_session, test_user.id, "Protected")
        project_id = project.id
        set_current_user_context(another_user)

        response = client.delete(f"/projects/{project_id}")

        assert response.status_code == 404

        # Verify project still exists
        set_current_user_context(test_user)
        verify_response = client.get(f"/projects/{project_id}")
        assert verify_response.status_code == 200

    def test_delete_project_without_auth(self, client: TestClient, db_session: Session, test_user: User):
        """Test deleting a project without authentication fails."""
        project = ProjectFactory.create(db_session, test_user.id, "To Delete")

        response = client.delete(f"/projects/{project.id}")

        assert response.status_code == 401


@pytest.mark.integration
class TestProjectsAPIWorkflow:
    """End-to-end workflow tests for projects API."""

    def test_complete_crud_workflow(self, client: TestClient, test_user: User):
        """Test complete CRUD workflow: create, read, update, delete."""
        set_current_user_context(test_user)

        # 1. Create a project
        create_response = client.post("/projects", json={"name": "Workflow Project"})
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # 2. Read the project
        get_response = client.get(f"/projects/{project_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Workflow Project"

        # 3. Update the project
        update_response = client.put(
            f"/projects/{project_id}",
            json={"name": "Updated Workflow Project"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Workflow Project"

        # 4. Delete the project
        delete_response = client.delete(f"/projects/{project_id}")
        assert delete_response.status_code == 204

        # 5. Verify it's gone
        verify_response = client.get(f"/projects/{project_id}")
        assert verify_response.status_code == 404

    def test_multi_user_isolation(self, client: TestClient, test_user: User, another_user: User):
        """Test that users' projects are properly isolated."""
        # User 1 creates projects
        set_current_user_context(test_user)
        client.post("/projects", json={"name": "User 1 Project 1"})
        client.post("/projects", json={"name": "User 1 Project 2"})

        user1_projects = client.get("/projects").json()
        assert len(user1_projects["data"]) == 2

        # User 2 creates projects
        set_current_user_context(another_user)
        client.post("/projects", json={"name": "User 2 Project 1"})

        user2_projects = client.get("/projects").json()
        assert len(user2_projects["data"]) == 1

        # Verify isolation
        assert user1_projects["data"][0]["id"] != user2_projects["data"][0]["id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
