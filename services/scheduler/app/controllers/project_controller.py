"""
Project controller for managing project CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.request.project_schemas import CreateProjectRequest, UpdateProjectRequest
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.schemas.response.project_schemas import ProjectResponse
from app.services.project_service import get_project_service
from db.client import client

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new project for the authenticated user.

    Args:
        request: Project creation request with name
        user: Current authenticated user
        db: Database session

    Returns:
        Created project data

    Raises:
        HTTPException: 401 if not authenticated
    """
    project_service = get_project_service(db)
    project = project_service.create_project(user_id=user.id, name=request.name)
    return project


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def get_projects(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max: 100)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all projects for the authenticated user with pagination.

    Args:
        page: Page number (default: 1, min: 1)
        page_size: Number of items per page (default: 10, max: 100)
        user: Current authenticated user
        db: Database session

    Returns:
        Paginated response with projects and pagination metadata including:
        - data: List of projects for the current page
        - pagination: Metadata with current_page, total_pages, total_entries,
          next_page, previous_page, has_next, has_previous

    Raises:
        HTTPException: 401 if not authenticated
    """
    project_service = get_project_service(db)
    projects, pagination_metadata = project_service.get_projects_paginated(
        user_id=user.id, page=page, page_size=page_size
    )

    # Convert projects to response models
    project_responses = [ProjectResponse.model_validate(project) for project in projects]

    return PaginatedResponse(
        data=project_responses,
        pagination=PaginationMetadata(**pagination_metadata),
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a specific project by ID.

    Args:
        project_id: ID of the project to retrieve
        user: Current authenticated user
        db: Database session

    Returns:
        Project data

    Raises:
        HTTPException: 401 if not authenticated, 404 if project not found or not owned by user
    """
    project_service = get_project_service(db)
    project = project_service.get_project(project_id=project_id, user_id=user.id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update an existing project.

    Args:
        project_id: ID of the project to update
        request: Project update request with new name
        user: Current authenticated user
        db: Database session

    Returns:
        Updated project data

    Raises:
        HTTPException: 401 if not authenticated, 404 if project not found or not owned by user
    """
    project_service = get_project_service(db)
    project = project_service.update_project(project_id=project_id, user_id=user.id, name=request.name)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a project.

    Args:
        project_id: ID of the project to delete
        user: Current authenticated user
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException: 401 if not authenticated, 404 if project not found or not owned by user
    """
    project_service = get_project_service(db)
    deleted = project_service.delete_project(project_id=project_id, user_id=user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )

    return None
