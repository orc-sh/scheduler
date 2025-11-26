"""
Load test controller for managing load/stress test operations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.celery import scheduler as celery_app
from app.middleware.auth_middleware import get_current_user
from app.models.collections import Collection
from app.models.load_test_reports import LoadTestReport
from app.models.load_test_runs import LoadTestRun
from app.models.user import User
from app.models.webhooks import Webhook
from app.schemas.request.load_test_schemas import (
    CreateCollectionRequest,
    CreateLoadTestRunRequest,
    CreateWebhookRequest,
    ReorderWebhooksRequest,
    UpdateCollectionRequest,
    UpdateWebhookRequest,
)
from app.schemas.response.load_test_schemas import (
    CollectionResponse,
    CollectionWithRunsResponse,
    LoadTestReportResponse,
    LoadTestReportWithResultsResponse,
    LoadTestRunResponse,
    LoadTestRunWithReportsResponse,
    WebhookResponse,
)
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.services.collection_service import get_collection_service
from app.services.load_test_service import get_load_test_service
from app.services.project_service import get_project_service
from app.services.webhook_service import get_webhook_service
from db.client import client

router = APIRouter()


def build_webhook_response(webhook: Webhook) -> WebhookResponse:
    """Build a WebhookResponse from Webhook."""
    return WebhookResponse(
        id=str(webhook.id),
        url=webhook.url,
        method=webhook.method,
        headers=webhook.headers,
        query_params=webhook.query_params,
        body_template=webhook.body_template,
        content_type=webhook.content_type,
        order=webhook.order,
    )


def build_collection_response(collection: Collection, include_webhooks: bool = True) -> CollectionResponse:
    """Build a CollectionResponse from Collection."""
    webhook_responses = []
    if include_webhooks and collection.webhooks:
        webhook_responses = [build_webhook_response(wh) for wh in collection.webhooks]

    return CollectionResponse(
        id=str(collection.id),
        project_id=str(collection.project_id),
        name=collection.name,
        description=collection.description,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        webhooks=webhook_responses,
    )


def build_run_response(run: LoadTestRun, include_collection: bool = False) -> LoadTestRunResponse:
    """Build a LoadTestRunResponse from LoadTestRun."""
    collection_response = None
    if include_collection and run.collection:
        collection_response = CollectionResponse(
            id=str(run.collection.id),
            name=run.collection.name,
            description=run.collection.description,
        )

    return LoadTestRunResponse(
        id=str(run.id),
        collection_id=str(run.collection_id),
        status=run.status,
        concurrent_users=run.concurrent_users,
        duration_seconds=run.duration_seconds,
        requests_per_second=run.requests_per_second,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        updated_at=run.updated_at,
        collection=collection_response,
    )


def build_report_response(report: LoadTestReport) -> LoadTestReportResponse:
    """Build a LoadTestReportResponse from LoadTestReport."""
    return LoadTestReportResponse(
        id=str(report.id),
        load_test_run_id=str(report.load_test_run_id),
        name=report.name,
        total_requests=report.total_requests,
        successful_requests=report.successful_requests,
        failed_requests=report.failed_requests,
        avg_response_time_ms=report.avg_response_time_ms,
        min_response_time_ms=report.min_response_time_ms,
        max_response_time_ms=report.max_response_time_ms,
        p95_response_time_ms=report.p95_response_time_ms,
        p99_response_time_ms=report.p99_response_time_ms,
        notes=report.notes,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


# Collection endpoints
@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/collections", response_model=PaginatedResponse[CollectionResponse])
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
        ),
    )


@router.get("/collections/{collection_id}", response_model=CollectionWithRunsResponse)
async def get_load_test_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a load test collection with its runs.

    Args:
        collection_id: ID of the collection
        user: Current authenticated user
        db: Database session

    Returns:
        Load test collection with runs
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
    load_test_service = get_load_test_service(db)
    runs = load_test_service.get_load_test_runs_by_collection(collection_id, skip=0, limit=100)

    config_response = build_collection_response(collection)
    return CollectionWithRunsResponse(
        **config_response.model_dump(),
        runs=[build_run_response(run) for run in runs],
    )


@router.put("/collections/{collection_id}", response_model=CollectionResponse)
async def update_load_test_collection(
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


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_load_test_collection(
    collection_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a load test collection and all its runs.

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
@router.post(
    "/collections/{collection_id}/runs", response_model=LoadTestRunResponse, status_code=status.HTTP_201_CREATED
)
async def create_load_test_run(
    collection_id: str,
    request: CreateLoadTestRunRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new load test run from a collection.

    Args:
        collection_id: ID of the collection
        request: Run creation request with execution parameters
        user: Current authenticated user
        db: Database session

    Returns:
        Created load test run
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
    load_test_service = get_load_test_service(db)
    run = load_test_service.create_load_test_run(
        collection_id,
        concurrent_users=request.concurrent_users,
        duration_seconds=request.duration_seconds,
        requests_per_second=request.requests_per_second,
    )

    # Start load test in background using Celery
    celery_app.send_task(
        "app.tasks.run_load_test.run_load_test",
        args=[str(run.id)],
        kwargs={},
    )

    return build_run_response(run)


@router.get("/collections/{collection_id}/runs", response_model=List[LoadTestRunResponse])
async def get_load_test_runs(
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
        List of load test runs
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

    load_test_service = get_load_test_service(db)
    runs = load_test_service.get_load_test_runs_by_collection(collection_id, skip=0, limit=100)

    return [build_run_response(run) for run in runs]


@router.get("/runs/{run_id}", response_model=LoadTestRunWithReportsResponse)
async def get_load_test_run(
    run_id: str,
    include_results: bool = Query(False, description="Include first page of results for each report"),
    results_page_size: int = Query(50, ge=1, le=100, description="Number of results per report"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a load test run with its reports.

    Args:
        run_id: ID of the run
        include_results: Whether to include first page of results for each report
        results_page_size: Number of results to include per report (max 100)
        user: Current authenticated user
        db: Database session

    Returns:
        Load test run with reports (optionally including results)
    """
    from app.schemas.response.load_test_schemas import LoadTestReportWithResultsResponse, LoadTestResultResponse

    load_test_service = get_load_test_service(db)
    run = load_test_service.get_load_test_run(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test run with ID '{run_id}' not found",
        )

    # Verify user has access through collection
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(run.collection_id)
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
    reports = load_test_service.get_load_test_reports_by_run(run_id, skip=0, limit=100)

    if include_results:
        # Include first page of results for each report
        report_responses = []
        for report in reports:
            # Get first page of results
            results = load_test_service.get_load_test_results(
                report.id,
                limit=results_page_size,
                offset=0,
            )

            result_responses = [
                LoadTestResultResponse(
                    id=str(r.id),
                    load_test_report_id=str(r.load_test_report_id),
                    endpoint_path=r.endpoint_path,
                    method=r.method,
                    request_headers=r.request_headers,
                    request_body=r.request_body,
                    response_status=r.response_status,
                    response_headers=r.response_headers,
                    response_body=r.response_body,
                    response_time_ms=r.response_time_ms,
                    error_message=r.error_message,
                    is_success=bool(r.is_success),
                    created_at=r.created_at,
                )
                for r in results
            ]

            # Build report response with results
            report_response = LoadTestReportWithResultsResponse(
                **build_report_response(report).model_dump(),
                results=result_responses,
            )
            report_responses.append(report_response)
    else:
        # Return reports without results
        report_responses = [
            LoadTestReportWithResultsResponse(
                **build_report_response(report).model_dump(),
                results=[],
            )
            for report in reports
        ]

    return LoadTestRunWithReportsResponse(
        **build_run_response(run).model_dump(),
        reports=report_responses,
    )


@router.post("/runs/{run_id}/run", response_model=LoadTestRunResponse)
async def run_load_test(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Manually trigger a load test run.

    Args:
        run_id: ID of the load test run to execute
        user: Current authenticated user
        db: Database session

    Returns:
        Load test run data
    """
    load_test_service = get_load_test_service(db)
    load_test_run = load_test_service.get_load_test_run(run_id)

    if not load_test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test run with ID '{run_id}' not found",
        )

    # Verify user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(load_test_run.collection_id)
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
            detail="You don't have permission to run this load test",
        )

    # Don't allow running if test is already running
    if load_test_run.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Load test is already running",
        )

    # Reset status to pending if it's completed or failed (allows re-running)
    if load_test_run.status in ("completed", "failed"):
        load_test_run.status = "pending"
        load_test_run.started_at = None
        load_test_run.completed_at = None

        # Delete old reports and results
        from app.models.load_test_results import LoadTestResult

        reports = load_test_service.get_load_test_reports_by_run(run_id, skip=0, limit=1000)
        for report in reports:
            # Delete results for this report
            db.query(LoadTestResult).filter(LoadTestResult.load_test_report_id == report.id).delete()
            # Delete report
            db.delete(report)

        db.commit()

    # Enqueue Celery task to run the load test
    celery_app.send_task(
        "app.tasks.run_load_test.run_load_test",
        args=[str(load_test_run.id)],
        kwargs={},
    )

    db.refresh(load_test_run)
    return build_run_response(load_test_run)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_load_test_run(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a load test run and all its reports.

    Args:
        run_id: ID of the run
        user: Current authenticated user
        db: Database session
    """
    load_test_service = get_load_test_service(db)
    load_test_run = load_test_service.get_load_test_run(run_id)

    if not load_test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test run with ID '{run_id}' not found",
        )

    # Verify user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(load_test_run.collection_id)
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

    load_test_service.delete_load_test_run(run_id)


# Report endpoints
@router.get("/runs/{run_id}/reports", response_model=List[LoadTestReportResponse])
async def get_load_test_reports(
    run_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all reports for a load test run.

    Args:
        run_id: ID of the run
        user: Current authenticated user
        db: Database session

    Returns:
        List of load test reports
    """
    load_test_service = get_load_test_service(db)
    run = load_test_service.get_load_test_run(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test run with ID '{run_id}' not found",
        )

    # Verify user has access
    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(run.collection_id)
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

    reports = load_test_service.get_load_test_reports_by_run(run_id, skip=0, limit=100)
    return [build_report_response(report) for report in reports]


@router.get("/reports/{report_id}", response_model=LoadTestReportWithResultsResponse)
async def get_load_test_report(
    report_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page (max: 100)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a load test report with its results.

    Args:
        report_id: ID of the report
        page: Page number for results
        page_size: Number of results per page
        user: Current authenticated user
        db: Database session

    Returns:
        Load test report with results
    """
    from app.schemas.response.load_test_schemas import LoadTestResultResponse

    load_test_service = get_load_test_service(db)
    report = db.query(LoadTestReport).filter(LoadTestReport.id == report_id).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test report with ID '{report_id}' not found",
        )

    # Verify user has access through run -> collection
    run = load_test_service.get_load_test_run(report.load_test_run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found for this report",
        )

    collection_service = get_collection_service(db)
    collection = collection_service.get_collection(run.collection_id)
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
    results = load_test_service.get_load_test_results(report_id, limit=page_size, offset=offset)

    result_responses = [
        LoadTestResultResponse(
            id=str(r.id),
            load_test_report_id=str(r.load_test_report_id),
            endpoint_path=r.endpoint_path,
            method=r.method,
            request_headers=r.request_headers,
            request_body=r.request_body,
            response_status=r.response_status,
            response_headers=r.response_headers,
            response_body=r.response_body,
            response_time_ms=r.response_time_ms,
            error_message=r.error_message,
            is_success=bool(r.is_success),
            created_at=r.created_at,
        )
        for r in results
    ]

    return LoadTestReportWithResultsResponse(
        **build_report_response(report).model_dump(),
        results=result_responses,
    )


# Webhook management endpoints
@router.post(
    "/collections/{collection_id}/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED
)
async def create_webhook(
    collection_id: str,
    request: CreateWebhookRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new webhook for a load test collection.

    Args:
        collection_id: ID of the load test collection
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
        order=request.order,
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
    if webhook.collection_id:
        collection_service = get_collection_service(db)
        collection = collection_service.get_collection(webhook.collection_id)
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
        order=request.order,
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
    if webhook.collection_id:
        collection_service = get_collection_service(db)
        collection = collection_service.get_collection(webhook.collection_id)
        if collection:
            project_service = get_project_service(db)
            project = project_service.get_project(str(collection.project_id), user.id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to delete this webhook",
                )

    webhook_service.delete_webhook(webhook_id)


@router.patch("/collections/{collection_id}/webhooks/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_webhooks(
    collection_id: str,
    request: ReorderWebhooksRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Reorder webhooks for a collection.

    Args:
        collection_id: ID of the collection
        request: Reorder request with webhook IDs in desired order
        user: Current authenticated user
        db: Database session
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

    # Reorder webhooks
    webhook_service = get_webhook_service(db)
    success = webhook_service.reorder_webhooks(collection_id, request.webhook_ids)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reorder webhooks. Ensure all webhook IDs belong to this collection.",
        )
