"""
Load test controller for managing load/stress test operations.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.celery import scheduler as celery_app
from app.middleware.auth_middleware import get_current_user
from app.models.load_test_configurations import LoadTestConfiguration
from app.models.load_test_reports import LoadTestReport
from app.models.load_test_runs import LoadTestRun
from app.models.user import User
from app.models.webhooks import Webhook
from app.schemas.request.load_test_schemas import CreateLoadTestConfigurationRequest, UpdateLoadTestConfigurationRequest
from app.schemas.response.load_test_schemas import (
    LoadTestConfigurationResponse,
    LoadTestConfigurationWithRunsResponse,
    LoadTestReportResponse,
    LoadTestReportWithResultsResponse,
    LoadTestRunResponse,
    LoadTestRunWithReportsResponse,
    WebhookResponse,
)
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.services.load_test_configuration_service import get_load_test_configuration_service
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
    )


def build_configuration_response(
    configuration: LoadTestConfiguration, include_webhook: bool = True
) -> LoadTestConfigurationResponse:
    """Build a LoadTestConfigurationResponse from LoadTestConfiguration."""
    webhook_response = None
    if include_webhook and configuration.webhook:
        webhook_response = build_webhook_response(configuration.webhook)

    return LoadTestConfigurationResponse(
        id=str(configuration.id),
        project_id=str(configuration.project_id),
        webhook_id=str(configuration.webhook_id),
        name=configuration.name,
        concurrent_users=configuration.concurrent_users,
        duration_seconds=configuration.duration_seconds,
        requests_per_second=configuration.requests_per_second,
        created_at=configuration.created_at,
        updated_at=configuration.updated_at,
        webhook=webhook_response,
    )


def build_run_response(run: LoadTestRun) -> LoadTestRunResponse:
    """Build a LoadTestRunResponse from LoadTestRun."""
    return LoadTestRunResponse(
        id=str(run.id),
        load_test_configuration_id=str(run.load_test_configuration_id),
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        updated_at=run.updated_at,
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


# Configuration endpoints
@router.post("/configurations", response_model=LoadTestConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def create_load_test_configuration(
    request: CreateLoadTestConfigurationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new load test configuration.

    Args:
        request: Load test configuration creation request
        user: Current authenticated user
        db: Database session

    Returns:
        Created load test configuration data
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

    # Validate endpoint requirements
    if not request.url or not request.method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="url and method are required",
        )

    # Create webhook configuration
    webhook_service = get_webhook_service(db)
    webhook = webhook_service.create_webhook(
        job_id=None,
        url=request.url,
        method=request.method,
        headers=request.headers,
        query_params=request.query_params,
        body_template=request.body_template,
        content_type=request.content_type or "application/json",
    )

    # Create load test configuration
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.create_configuration(
        project_id=project_id,
        webhook_id=str(webhook.id),
        name=request.name,
        concurrent_users=request.concurrent_users,
        duration_seconds=request.duration_seconds,
        requests_per_second=request.requests_per_second,
    )

    # Refresh to get webhook relationship
    db.refresh(configuration)
    if configuration.webhook is None:
        db.refresh(webhook)
        configuration.webhook = webhook

    return build_configuration_response(configuration)


@router.get("/configurations", response_model=PaginatedResponse[LoadTestConfigurationResponse])
async def get_load_test_configurations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max: 100)"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all load test configurations with pagination.

    Args:
        page: Page number
        page_size: Number of items per page
        project_id: Optional project ID filter
        user: Current authenticated user
        db: Database session

    Returns:
        Paginated list of load test configurations
    """
    project_service = get_project_service(db)
    config_service = get_load_test_configuration_service(db)

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

    # Get configurations for user's projects
    skip = (page - 1) * page_size
    all_configs = []
    for pid in project_ids:
        configs = config_service.get_configurations_by_project(pid, skip=0, limit=1000)
        all_configs.extend(configs)

    # Manual pagination
    total_items = len(all_configs)
    total_pages = (total_items + page_size - 1) // page_size
    paginated_configs = all_configs[skip : skip + page_size]

    # Build responses with webhooks
    for config in paginated_configs:
        if config.webhook is None:
            webhook = db.query(Webhook).filter(Webhook.id == config.webhook_id).first()
            if webhook:
                config.webhook = webhook

    return PaginatedResponse(
        data=[build_configuration_response(c) for c in paginated_configs],
        pagination=PaginationMetadata(
            current_page=page,
            page_size=page_size,
            total_entries=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )


@router.get("/configurations/{config_id}", response_model=LoadTestConfigurationWithRunsResponse)
async def get_load_test_configuration(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a load test configuration with its runs.

    Args:
        config_id: ID of the configuration
        user: Current authenticated user
        db: Database session

    Returns:
        Load test configuration with runs
    """
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(config_id)

    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test configuration with ID '{config_id}' not found",
        )

    # Verify user has access through project
    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this configuration",
        )

    # Get webhook
    if configuration.webhook is None:
        webhook = db.query(Webhook).filter(Webhook.id == configuration.webhook_id).first()
        if webhook:
            configuration.webhook = webhook

    # Get runs
    load_test_service = get_load_test_service(db)
    runs = load_test_service.get_load_test_runs_by_configuration(config_id, skip=0, limit=100)

    config_response = build_configuration_response(configuration)
    return LoadTestConfigurationWithRunsResponse(
        **config_response.model_dump(),
        runs=[build_run_response(run) for run in runs],
    )


@router.put("/configurations/{config_id}", response_model=LoadTestConfigurationResponse)
async def update_load_test_configuration(
    config_id: str,
    request: UpdateLoadTestConfigurationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update a load test configuration.

    Args:
        config_id: ID of the configuration
        request: Update request
        user: Current authenticated user
        db: Database session

    Returns:
        Updated configuration
    """
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(config_id)

    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test configuration with ID '{config_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this configuration",
        )

    updated_config = config_service.update_configuration(
        config_id,
        name=request.name,
        concurrent_users=request.concurrent_users,
        duration_seconds=request.duration_seconds,
        requests_per_second=request.requests_per_second,
    )

    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test configuration with ID '{config_id}' not found",
        )

    if updated_config.webhook is None:
        webhook = db.query(Webhook).filter(Webhook.id == updated_config.webhook_id).first()
        if webhook:
            updated_config.webhook = webhook

    return build_configuration_response(updated_config)


@router.delete("/configurations/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_load_test_configuration(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a load test configuration and all its runs.

    Args:
        config_id: ID of the configuration
        user: Current authenticated user
        db: Database session
    """
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(config_id)

    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test configuration with ID '{config_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this configuration",
        )

    config_service.delete_configuration(config_id)


# Run endpoints
@router.post(
    "/configurations/{config_id}/runs", response_model=LoadTestRunResponse, status_code=status.HTTP_201_CREATED
)
async def create_load_test_run(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new load test run from a configuration.

    Args:
        config_id: ID of the load test configuration
        user: Current authenticated user
        db: Database session

    Returns:
        Created load test run
    """
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(config_id)

    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test configuration with ID '{config_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create runs for this configuration",
        )

    # Create run
    load_test_service = get_load_test_service(db)
    run = load_test_service.create_load_test_run(config_id)

    # Start load test in background using Celery
    celery_app.send_task(
        "app.tasks.run_load_test.run_load_test",
        args=[str(run.id)],
        kwargs={},
    )

    return build_run_response(run)


@router.get("/configurations/{config_id}/runs", response_model=List[LoadTestRunResponse])
async def get_load_test_runs(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all runs for a configuration.

    Args:
        config_id: ID of the configuration
        user: Current authenticated user
        db: Database session

    Returns:
        List of load test runs
    """
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(config_id)

    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Load test configuration with ID '{config_id}' not found",
        )

    # Verify user has access
    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this configuration",
        )

    load_test_service = get_load_test_service(db)
    runs = load_test_service.get_load_test_runs_by_configuration(config_id, skip=0, limit=100)

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

    # Verify user has access through configuration
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(run.load_test_configuration_id)
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
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
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(load_test_run.load_test_configuration_id)
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
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
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(load_test_run.load_test_configuration_id)
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
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
    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(run.load_test_configuration_id)
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found for this run",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
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

    # Verify user has access through run -> configuration
    run = load_test_service.get_load_test_run(report.load_test_run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found for this report",
        )

    config_service = get_load_test_configuration_service(db)
    configuration = config_service.get_configuration(run.load_test_configuration_id)
    if not configuration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found",
        )

    project_service = get_project_service(db)
    project = project_service.get_project(str(configuration.project_id), user.id)
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
