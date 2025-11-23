"""
Webhook controller for managing Cron webhook integrations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.request.webhook_schemas import CreateCronWebhookRequest, UpdateWebhookRequest
from app.schemas.response.webhook_schemas import CronWebhookResponse, WebhookResponse
from app.services.job_service import get_job_service
from app.services.project_service import get_project_service
from app.services.webhook_service import get_webhook_service
from db.client import client

router = APIRouter()


@router.post("", response_model=CronWebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_cron_webhook(
    request: CreateCronWebhookRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a webhook with associated job and project via Cron integration.

    This endpoint:
    1. Uses the authenticated user's name as the project name
    2. Gets or creates a project with that name
    3. Creates a job linked to the project
    4. Creates a webhook linked to the job

    Args:
        request: Cron webhook creation request containing job and webhook data
        user: Current authenticated user (automatically extracted from JWT)
        db: Database session

    Returns:
        Combined response with project, job, and webhook data

    Raises:
        HTTPException: 401 if not authenticated, 400 if validation fails
    """
    try:
        # Step 1: Get or create project using user's name
        project_service = get_project_service(db)
        project = project_service.get_or_create_project_by_name(user_id=user.id, project_name=user.name)

        # Step 2: Create job for the project
        job_service = get_job_service(db)
        job = job_service.create_job(
            project_id=str(project.id),
            name=request.job.name,
            schedule=request.job.schedule,
            job_type=request.job.type,
            timezone=request.job.timezone,
            enabled=request.job.enabled,
        )

        # Step 3: Create webhook for the job
        webhook_service = get_webhook_service(db)
        webhook = webhook_service.create_webhook(
            job_id=str(job.id),
            url=request.webhook.url,
            method=request.webhook.method,
            headers=request.webhook.headers,
            query_params=request.webhook.query_params,
            body_template=request.webhook.body_template,
            content_type=request.webhook.content_type,
        )

        # Return combined response
        return CronWebhookResponse(
            project=project,
            job=job,
            webhook=webhook,
        )

    except ValueError as e:
        # Handle validation errors (e.g., invalid cron expression)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook: {str(e)}",
        )


@router.get("/{webhook_id}", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def get_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a specific webhook by ID.

    Args:
        webhook_id: ID of the webhook to retrieve
        user: Current authenticated user (automatically extracted from JWT)
        db: Database session

    Returns:
        Webhook details

    Raises:
        HTTPException: 401 if not authenticated, 404 if webhook not found
    """
    try:
        webhook_service = get_webhook_service(db)
        webhook = webhook_service.get_webhook(webhook_id)

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with ID {webhook_id} not found",
            )

        # Verify user has access to this webhook (through job and project)
        job_service = get_job_service(db)
        job = job_service.get_job(str(webhook.job_id))
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated job not found",
            )

        project_service = get_project_service(db)
        project = project_service.get_project(str(job.project_id), user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this webhook",
            )

        # Include job information in response
        from app.schemas.response.webhook_schemas import WebhookResponse

        webhook_dict = {
            "id": str(webhook.id),
            "job_id": str(webhook.job_id),
            "url": webhook.url,
            "method": webhook.method,
            "headers": webhook.headers,
            "query_params": webhook.query_params,
            "body_template": webhook.body_template,
            "content_type": webhook.content_type,
            "created_at": webhook.created_at,
            "updated_at": webhook.updated_at,
            "job": job,
        }
        return WebhookResponse(**webhook_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve webhook: {str(e)}",
        )


@router.get("", response_model=list[WebhookResponse], status_code=status.HTTP_200_OK)
async def get_all_webhooks(
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
    limit: int = 100,
    offset: int = 0,
):
    """
    Get all webhooks for the authenticated user.

    This endpoint returns all webhooks that belong to jobs in the user's projects.

    Args:
        user: Current authenticated user (automatically extracted from JWT)
        db: Database session
        limit: Maximum number of webhooks to return (default: 100)
        offset: Number of webhooks to skip (default: 0)

    Returns:
        List of webhook details

    Raises:
        HTTPException: 401 if not authenticated
    """
    try:
        # Get all projects for the user
        project_service = get_project_service(db)
        projects = project_service.get_projects(user.id)

        # Get all jobs for these projects
        job_service = get_job_service(db)
        webhook_service = get_webhook_service(db)
        all_webhooks = []

        for project in projects:
            project_id = str(project.id)
            jobs = job_service.get_jobs_by_project(project_id)
            for job in jobs:
                job_id = str(job.id)
                webhooks = webhook_service.get_webhooks_by_job(job_id)
                # Include job information with each webhook
                for webhook in webhooks:
                    webhook_dict = {
                        "id": str(webhook.id),
                        "job_id": str(webhook.job_id),
                        "url": webhook.url,
                        "method": webhook.method,
                        "headers": webhook.headers,
                        "query_params": webhook.query_params,
                        "body_template": webhook.body_template,
                        "content_type": webhook.content_type,
                        "created_at": webhook.created_at,
                        "updated_at": webhook.updated_at,
                        "job": job,
                    }
                    all_webhooks.append(WebhookResponse(**webhook_dict))

        # Apply pagination
        paginated_webhooks = all_webhooks[offset : offset + limit]

        return paginated_webhooks

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve webhooks: {str(e)}",
        )


@router.put("/{webhook_id}", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update a webhook's properties.

    Args:
        webhook_id: ID of the webhook to update
        request: Update request containing fields to modify
        user: Current authenticated user (automatically extracted from JWT)
        db: Database session

    Returns:
        Updated webhook details

    Raises:
        HTTPException: 401 if not authenticated, 403 if no permission, 404 if webhook not found
    """
    try:
        webhook_service = get_webhook_service(db)
        webhook = webhook_service.get_webhook(webhook_id)

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with ID {webhook_id} not found",
            )

        # Verify user has access to this webhook (through job and project)
        job_service = get_job_service(db)
        job = job_service.get_job(str(webhook.job_id))
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated job not found",
            )

        project_service = get_project_service(db)
        project = project_service.get_project(str(job.project_id), user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this webhook",
            )

        # Update job if job fields are provided
        if request.job:
            updated_job = job_service.update_job(
                job_id=str(job.id),
                name=request.job.name,
                schedule=request.job.schedule,
                timezone=request.job.timezone,
                enabled=request.job.enabled,
            )
            if updated_job:
                job = updated_job

        # Update webhook
        updated_webhook = webhook_service.update_webhook(
            webhook_id=webhook_id,
            url=request.url,
            method=request.method,
            headers=request.headers,
            query_params=request.query_params,
            body_template=request.body_template,
            content_type=request.content_type,
        )

        if not updated_webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with ID {webhook_id} not found",
            )

        # Include job information in response
        webhook_dict = {
            "id": str(updated_webhook.id),
            "job_id": str(updated_webhook.job_id),
            "url": updated_webhook.url,
            "method": updated_webhook.method,
            "headers": updated_webhook.headers,
            "query_params": updated_webhook.query_params,
            "body_template": updated_webhook.body_template,
            "content_type": updated_webhook.content_type,
            "created_at": updated_webhook.created_at,
            "updated_at": updated_webhook.updated_at,
            "job": job,
        }
        return WebhookResponse(**webhook_dict)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook: {str(e)}",
        )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a webhook.

    Args:
        webhook_id: ID of the webhook to delete
        user: Current authenticated user (automatically extracted from JWT)
        db: Database session

    Returns:
        No content (204) on success

    Raises:
        HTTPException: 401 if not authenticated, 403 if no permission, 404 if webhook not found
    """
    try:
        webhook_service = get_webhook_service(db)
        webhook = webhook_service.get_webhook(webhook_id)

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with ID {webhook_id} not found",
            )

        # Verify user has access to this webhook (through job and project)
        job_service = get_job_service(db)
        job = job_service.get_job(str(webhook.job_id))
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated job not found",
            )

        project_service = get_project_service(db)
        project = project_service.get_project(str(job.project_id), user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this webhook",
            )

        # Delete webhook
        result = webhook_service.delete_webhook(webhook_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with ID {webhook_id} not found",
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook: {str(e)}",
        )
