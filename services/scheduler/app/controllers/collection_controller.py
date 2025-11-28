"""
Collection controller for managing collection operations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.celery import scheduler as celery_app
from app.middleware.auth_middleware import get_current_user
from app.models.collection_reports import CollectionReport
from app.models.collection_runs import CollectionRun
from app.models.collections import Collection
from app.models.user import User
from app.models.webhooks import Webhook
from app.schemas.request.collection_schemas import (
    CreateCollectionRequest,
    CreateCollectionRunRequest,
    CreateWebhookRequest,
    UpdateCollectionRequest,
    UpdateWebhookRequest,
)
from app.schemas.response.collection_schemas import (
    CollectionReportResponse,
    CollectionReportWithResultsResponse,
    CollectionResponse,
    CollectionRunResponse,
    CollectionRunWithReportsResponse,
    CollectionWithRunsResponse,
    WebhookResponse,
)
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.services.collection_service import get_collection_service
from app.services.project_service import get_project_service
from app.services.webhook_service import get_webhook_service
from db.client import client

router = APIRouter()


def build_webhook_response(webhook: Webhook) -> WebhookResponse:
    """Build a WebhookResponse from Webhook."""
    return WebhookResponse(
        id=str(webhook.id),
        url=str(webhook.url) if webhook.url else "",  # type: ignore[truthy-function]
        method=str(webhook.method) if webhook.method else "POST",  # type: ignore[truthy-function]
        headers=webhook.headers,  # type: ignore[arg-type]
        query_params=webhook.query_params,  # type: ignore[arg-type]
        body_template=webhook.body_template,  # type: ignore[arg-type]
        content_type=webhook.content_type,  # type: ignore[arg-type]
    )


def build_collection_response(collection: Collection, include_webhooks: bool = True) -> CollectionResponse:
    """Build a CollectionResponse from Collection."""
    webhook_responses = []
    if include_webhooks and collection.webhooks:
        webhook_responses = [build_webhook_response(wh) for wh in collection.webhooks]

    return CollectionResponse(
        id=str(collection.id),
        project_id=str(collection.project_id),
        name=collection.name,  # type: ignore[arg-type]
        description=collection.description,  # type: ignore[arg-type]
        created_at=collection.created_at,  # type: ignore[arg-type]
        updated_at=collection.updated_at,  # type: ignore[arg-type]
        webhooks=webhook_responses,
    )


def build_run_response(run: CollectionRun, include_collection: bool = False) -> CollectionRunResponse:
    """Build a CollectionRunResponse from CollectionRun."""
    collection_response = None
    if include_collection and run.collection:
        collection_response = CollectionResponse(
            id=str(run.collection.id),
            name=run.collection.name,
            description=run.collection.description,
        )

    return CollectionRunResponse(
        id=str(run.id),
        collection_id=str(run.collection_id),
        status=str(run.status) if run.status else "pending",  # type: ignore[truthy-function]
        concurrent_users=(
            int(run.concurrent_users) if run.concurrent_users else 0
        ),  # type: ignore[truthy-function,arg-type]
        duration_seconds=(
            int(run.duration_seconds) if run.duration_seconds else 0
        ),  # type: ignore[truthy-function,arg-type]
        requests_per_second=int(run.requests_per_second) if run.requests_per_second else None,  # type: ignore[arg-type]
        started_at=run.started_at,  # type: ignore[arg-type]
        completed_at=run.completed_at,  # type: ignore[arg-type]
        created_at=run.created_at,  # type: ignore[arg-type]
        updated_at=run.updated_at,  # type: ignore[arg-type]
        collection=collection_response,
    )


def build_report_response(report: CollectionReport) -> CollectionReportResponse:
    """Build a CollectionReportResponse from CollectionReport."""
    return CollectionReportResponse(
        id=str(report.id),
        collection_run_id=str(report.collection_run_id),
        name=report.name,  # type: ignore[arg-type]
        total_requests=(
            int(report.total_requests) if report.total_requests else 0
        ),  # type: ignore[truthy-function,arg-type]
        successful_requests=(
            int(report.successful_requests) if report.successful_requests else 0
        ),  # type: ignore[truthy-function,arg-type]
        failed_requests=(
            int(report.failed_requests) if report.failed_requests else 0
        ),  # type: ignore[truthy-function,arg-type]
        avg_response_time_ms=(
            int(report.avg_response_time_ms) if report.avg_response_time_ms else None
        ),  # type: ignore[truthy-function,arg-type]
        min_response_time_ms=(
            int(report.min_response_time_ms) if report.min_response_time_ms else None
        ),  # type: ignore[truthy-function,arg-type]
        max_response_time_ms=(
            int(report.max_response_time_ms) if report.max_response_time_ms else None
        ),  # type: ignore[truthy-function,arg-type]
        p95_response_time_ms=(
            int(report.p95_response_time_ms) if report.p95_response_time_ms else None
        ),  # type: ignore[truthy-function,arg-type]
        p99_response_time_ms=(
            int(report.p99_response_time_ms) if report.p99_response_time_ms else None
        ),  # type: ignore[truthy-function,arg-type]
        notes=report.notes,  # type: ignore[arg-type]
        created_at=report.created_at,  # type: ignore[arg-type]
        updated_at=report.updated_at,  # type: ignore[arg-type]
    )


# Collection endpoints
@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CreateCollectionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new webhook collection.

    Args:
        request: Collection creation request
        user: Current authenticated user
        db: Database session

    Returns:
        Created collection data
    """
    # Get or create project for user
    project_service = get_project_service(db)

    if request.project_id:
        project = project_service.get_project(project_id=request.project_id, user_id=user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{request.project_id}' not found",
            )
    else:
        projects = project_service.get_projects(user.id, skip=0, limit=1)
        if projects:
            project = projects[0]
        else:
            project = project_service.create_project(user_id=user.id, name="Default Project")

    project_id = str(project.id)

    # Create webhook collection
    collection_service = get_collection_service(db)
    collection = collection_service.create_collection(
        project_id=project_id,
        name=request.name,
        description=request.description,
    )

    # Refresh to get relationships
    db.refresh(collection)

    return build_collection_response(collection)


@router.get("/", response_model=PaginatedResponse[CollectionResponse])
async def get_collections(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max: 100)"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all collections with pagination.

    Args:
        page: Page number
        page_size: Number of items per page
        project_id: Optional project ID filter
        user: Current authenticated user
        db: Database session

    Returns:
        Paginated list of collections
    """
    project_service = get_project_service(db)
    collection_service = get_collection_service(db)

    # Get user's projects if project_id not specified
    if project_id:
        project = project_service.get_project(project_id=project_id, user_id=user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found",
            )
        project_ids = [project_id]
    else:
        projects = project_service.get_projects(user.id, skip=0, limit=100)
        project_ids = [str(p.id) for p in projects]

    if not project_ids:
        return PaginatedResponse(
            data=[],
            pagination=PaginationMetadata(
                current_page=page,
                page_size=page_size,
                total_entries=0,
                total_pages=0,
                has_next=False,
                has_previous=False,
                next_page=None,
                previous_page=None,
            ),
        )

    # Get collections for user's projects
    skip = (page - 1) * page_size
    all_collections = []
    for pid in project_ids:
        collections = collection_service.get_collections_by_project(pid, skip=0, limit=1000)
        all_collections.extend(collections)

    # Manual pagination
    total_items = len(all_collections)
    total_pages = (total_items + page_size - 1) // page_size
    paginated_collections = all_collections[skip : skip + page_size]

    # Load webhooks for collections
    webhook_service = get_webhook_service(db)
    for collection in paginated_collections:
        if not collection.webhooks:
            webhooks = webhook_service.get_webhooks_by_collection(str(collection.id))
            collection.webhooks = webhooks

    return PaginatedResponse(
        data=[build_collection_response(c) for c in paginated_collections],
        pagination=PaginationMetadata(
            current_page=page,
            page_size=page_size,
            total_entries=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
            next_page=page + 1 if page < total_pages else None,
            previous_page=page - 1 if page > 1 else None,
        ),
    )


@router.get("/{collection_id}", response_model=CollectionWithRunsResponse)
async def get_collection_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a collection collection with its runs.

    Args:
        collection_id: ID of the collection
        user: Current authenticated user
        db: Database session

    Returns:
        Collection collection with runs
    """
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    # Verify user has access through project
    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this collection",
        )

    # Get webhooks
    webhook_service = get_webhook_service(db)
    if not collection.webhooks:
        webhooks = webhook_service.get_webhooks_by_collection(collection_id)
        collection.webhooks = webhooks

    # Get runs
    collection_service = get_collection_service(db)
    runs = collection_service.get_collection_runs_by_collection(collection_id, skip=0, limit=100)

    config_response = build_collection_response(collection)
    return CollectionWithRunsResponse(
        **config_response.model_dump(),
        runs=[build_run_response(run) for run in runs],
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection_collection(
    collection_id: str,
    request: UpdateCollectionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update a webhook collection.

    Args:
        collection_id: ID of the collection
        request: Update request
        user: Current authenticated user
        db: Database session

    Returns:
        Updated collection
    """
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this collection",
        )

    updated_config = collection_service.update_collection(
        collection_id,
        name=request.name,
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    # Load webhooks
    webhook_service = get_webhook_service(db)
    if not updated_config.webhooks:
        webhooks = webhook_service.get_webhooks_by_collection(collection_id)
        updated_config.webhooks = webhooks

    return build_collection_response(updated_config)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a collection collection and all its runs.

    Args:
        collection_id: ID of the collection
        user: Current authenticated user
        db: Database session
    """
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this collection",
        )

    collection_service.delete_collection(collection_id)


# Run endpoints
@router.post("/{collection_id}/runs", response_model=CollectionRunResponse, status_code=status.HTTP_201_CREATED)
async def create_collection_run(
    collection_id: str,
    request: CreateCollectionRunRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new collection run from a collection.

    Args:
        collection_id: ID of the collection
        request: Run creation request with execution parameters
        user: Current authenticated user
        db: Database session

    Returns:
        Created collection run
    """
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create runs for this collection",
        )

    # Create run with execution parameters
    collection_service = get_collection_service(db)
    run = collection_service.create_collection_run(
        collection_id,
        concurrent_users=request.concurrent_users,
        duration_seconds=request.duration_seconds,
        requests_per_second=request.requests_per_second,
    )

    # Start collection in background using Celery
    celery_app.send_task(
        "app.tasks.run_collection.run_collection",
        args=[str(run.id)],
        kwargs={},
    )

    return build_run_response(run)


@router.get("/{collection_id}/runs", response_model=List[CollectionRunResponse])
async def get_collection_runs(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all runs for a collection.

    Args:
        collection_id: ID of the collection
        user: Current authenticated user
        db: Database session

    Returns:
        List of collection runs
    """
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this collection",
        )

    collection_service = get_collection_service(db)
    runs = collection_service.get_collection_runs_by_collection(collection_id, skip=0, limit=100)

    return [build_run_response(run) for run in runs]


@router.get("/runs/{run_id}", response_model=CollectionRunWithReportsResponse)
async def get_collection_run(
    run_id: str,
    include_results: bool = Query(False, description="Include first page of results for each report"),
    results_page_size: int = Query(50, ge=1, le=100, description="Number of results per report"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a collection run with its reports.

    Args:
        run_id: ID of the run
        include_results: Whether to include first page of results for each report
        results_page_size: Number of results to include per report (max 100)
        user: Current authenticated user
        db: Database session

    Returns:
        Collection run with reports (optionally including results)
    """
    from app.schemas.response.collection_schemas import CollectionReportWithResultsResponse, CollectionResultResponse

    collection_service = get_collection_service(db)
    run = collection_service.get_collection_run(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection run with ID '{run_id}' not found",
        )

    # Verify user has access through collection
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(str(run.collection_id))
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this run",
        )

    # Get reports
    reports = collection_service.get_collection_reports_by_run(run_id, skip=0, limit=100)

    if include_results:
        # Include first page of results for each report
        report_responses = []
        for report in reports:
            # Get first page of results
            results = collection_service.get_collection_results(
                str(report.id),
                limit=results_page_size,
                offset=0,
            )

            result_responses = [
                CollectionResultResponse(
                    id=str(r.id),
                    collection_report_id=str(r.collection_report_id),
                    endpoint_path=str(r.endpoint_path) if r.endpoint_path else "",  # type: ignore[truthy-function]
                    method=str(r.method) if r.method else "GET",  # type: ignore[truthy-function]
                    request_headers=r.request_headers,  # type: ignore[arg-type]
                    request_body=r.request_body,  # type: ignore[arg-type]
                    response_status=(
                        int(r.response_status) if r.response_status else None
                    ),  # type: ignore[truthy-function,arg-type]
                    response_headers=r.response_headers,  # type: ignore[arg-type]
                    response_body=r.response_body,  # type: ignore[arg-type]
                    response_time_ms=(
                        int(r.response_time_ms) if r.response_time_ms else 0
                    ),  # type: ignore[truthy-function,arg-type]
                    error_message=r.error_message,  # type: ignore[arg-type]
                    is_success=bool(r.is_success),
                    created_at=r.created_at,  # type: ignore[arg-type]
                )
                for r in results
            ]

            # Build report response with results
            report_response = CollectionReportWithResultsResponse(
                **build_report_response(report).model_dump(),
                results=result_responses,
            )
            report_responses.append(report_response)
    else:
        # Return reports without results
        report_responses = [
            CollectionReportWithResultsResponse(
                **build_report_response(report).model_dump(),
                results=[],
            )
            for report in reports
        ]

    return CollectionRunWithReportsResponse(
        **build_run_response(run).model_dump(),
        reports=report_responses,
    )


@router.post("/runs/{run_id}/run", response_model=CollectionRunResponse)
async def run_collection(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Manually trigger a collection run.

    Args:
        run_id: ID of the collection run to execute
        user: Current authenticated user
        db: Database session

    Returns:
        Collection run data
    """
    collection_service = get_collection_service(db)
    collection_run = collection_service.get_collection_run(run_id)

    if not collection_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection run with ID '{run_id}' not found",
        )

    # Verify user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(str(collection_run.collection_id))
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to run this collection",
        )

    # Don't allow running if test is already running
    if str(collection_run.status) == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Collection is already running",
        )

    # Reset status to pending if it's completed or failed (allows re-running)
    if str(collection_run.status) in ("completed", "failed"):
        collection_run.status = "pending"  # type: ignore[assignment]
        collection_run.started_at = None  # type: ignore[assignment]
        collection_run.completed_at = None  # type: ignore[assignment]

        # Delete old reports and results
        from app.models.collection_results import CollectionResult

        reports = collection_service.get_collection_reports_by_run(run_id, skip=0, limit=1000)
        for report in reports:
            # Delete results for this report
            db.query(CollectionResult).filter(CollectionResult.collection_report_id == report.id).delete()
            # Delete report
            db.delete(report)

        db.commit()

    # Enqueue Celery task to run the collection
    celery_app.send_task(
        "app.tasks.run_collection.run_collection",
        args=[str(collection_run.id)],
        kwargs={},
    )

    db.refresh(collection_run)
    return build_run_response(collection_run)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a collection run and all its reports.

    Args:
        run_id: ID of the run
        user: Current authenticated user
        db: Database session
    """
    collection_service = get_collection_service(db)
    collection_run = collection_service.get_collection_run(run_id)

    if not collection_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection run with ID '{run_id}' not found",
        )

    # Verify user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(str(collection_run.collection_id))
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this run",
        )

    collection_service.delete_collection_run(run_id)


# Report endpoints
@router.get("/runs/{run_id}/reports", response_model=List[CollectionReportResponse])
async def get_collection_reports(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all reports for a collection run.

    Args:
        run_id: ID of the run
        user: Current authenticated user
        db: Database session

    Returns:
        List of collection reports
    """
    collection_service = get_collection_service(db)
    run = collection_service.get_collection_run(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection run with ID '{run_id}' not found",
        )

    # Verify user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(str(run.collection_id))
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this run",
        )

    reports = collection_service.get_collection_reports_by_run(run_id, skip=0, limit=100)
    return [build_report_response(report) for report in reports]


@router.get("/reports/{report_id}", response_model=CollectionReportWithResultsResponse)
async def get_collection_report(
    report_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page (max: 100)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a collection report with its results.

    Args:
        report_id: ID of the report
        page: Page number for results
        page_size: Number of results per page
        user: Current authenticated user
        db: Database session

    Returns:
        Collection report with results
    """
    from app.schemas.response.collection_schemas import CollectionResultResponse

    collection_service = get_collection_service(db)
    report = db.query(CollectionReport).filter(CollectionReport.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection report with ID '{report_id}' not found",
        )

    # Verify user has access through run -> collection
    run = collection_service.get_collection_run(str(report.collection_run_id))
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found for this report",
        )

    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(str(run.collection_id))
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this report",
        )

    # Get results
    offset = (page - 1) * page_size
    results = collection_service.get_collection_results(report_id, limit=page_size, offset=offset)

    result_responses = [
        CollectionResultResponse(
            id=str(r.id),
            collection_report_id=str(r.collection_report_id),
            endpoint_path=str(r.endpoint_path) if r.endpoint_path else "",  # type: ignore[truthy-function]
            method=str(r.method) if r.method else "GET",  # type: ignore[truthy-function]
            request_headers=r.request_headers,  # type: ignore[arg-type]
            request_body=r.request_body,  # type: ignore[arg-type]
            response_status=(
                int(r.response_status) if r.response_status else None
            ),  # type: ignore[truthy-function,arg-type]
            response_headers=r.response_headers,  # type: ignore[arg-type]
            response_body=r.response_body,  # type: ignore[arg-type]
            response_time_ms=(
                int(r.response_time_ms) if r.response_time_ms else 0
            ),  # type: ignore[truthy-function,arg-type]
            error_message=r.error_message,  # type: ignore[arg-type]
            is_success=bool(r.is_success),
            created_at=r.created_at,  # type: ignore[arg-type]
        )
        for r in results
    ]

    return CollectionReportWithResultsResponse(
        **build_report_response(report).model_dump(),
        results=result_responses,
    )


# Webhook management endpoints
@router.post("/{collection_id}/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    collection_id: str,
    request: CreateWebhookRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new webhook for a collection collection.

    Args:
        collection_id: ID of the collection collection
        request: Webhook creation request
        user: Current authenticated user
        db: Database session

    Returns:
        Created webhook data
    """
    # Verify collection exists and user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection with ID '{collection_id}' not found",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(collection.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this collection",
        )

    # Create webhook
    webhook_service = get_webhook_service(db)
    webhook = webhook_service.create_webhook(
        collection_id=collection_id,
        url=request.url,
        method=request.method,
        headers=request.headers,
        query_params=request.query_params,
        body_template=request.body_template,
        content_type=request.content_type or "application/json",
    )

    return build_webhook_response(webhook)


@router.put("/webhooks/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update a webhook.

    Args:
        webhook_id: ID of the webhook
        request: Webhook update request
        user: Current authenticated user
        db: Database session

    Returns:
        Updated webhook data
    """
    webhook_service = get_webhook_service(db)
    webhook = webhook_service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with ID '{webhook_id}' not found",
        )

    # Verify user has access through collection
    if webhook.collection_id:  # type: ignore[truthy-function]
        collection_service = get_collection_service(db)
        collection = collection_service.get_collection(str(webhook.collection_id))
        if collection:
            project_service = get_project_service(db)
            project = project_service.get_project(str(collection.project_id), user.id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to update this webhook",
                )

    # Update webhook
    updated_webhook = webhook_service.update_webhook(
        webhook_id,
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
            detail=f"Webhook with ID '{webhook_id}' not found",
        )

    return build_webhook_response(updated_webhook)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a webhook.

    Args:
        webhook_id: ID of the webhook
        user: Current authenticated user
        db: Database session
    """
    webhook_service = get_webhook_service(db)
    webhook = webhook_service.get_webhook(webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook with ID '{webhook_id}' not found",
        )

    # Verify user has access through collection
    if webhook.collection_id:  # type: ignore[truthy-function]
        collection_service = get_collection_service(db)
        collection = collection_service.get_collection(str(webhook.collection_id))
        if collection:
            project_service = get_project_service(db)
            project = project_service.get_project(str(collection.project_id), user.id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this webhook",
                )

    webhook_service.delete_webhook(webhook_id)
