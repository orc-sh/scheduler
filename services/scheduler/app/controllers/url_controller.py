"""
URL controller for managing URL endpoints and logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.request.url_schemas import CreateUrlRequest
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.schemas.response.url_schemas import UrlLogResponse, UrlResponse, UrlWithLogsResponse
from app.services.account_service import get_account_service
from app.services.rate_limiter_service import get_rate_limiter_service
from app.services.url_service import get_url_service
from db.client import client

router = APIRouter()


@router.post("", response_model=UrlResponse, status_code=status.HTTP_201_CREATED)
async def create_url(
    request: CreateUrlRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new URL for the authenticated user's account.

    Args:
        request: URL creation request with account_id
        user: Current authenticated user
        db: Database session

    Returns:
        Created URL data with path

    Raises:
        HTTPException: 401 if not authenticated, 404 if account not found
    """
    # Verify account exists and belongs to user
    account_service = get_account_service(db)
    account = account_service.get_or_create_account_by_name(user_id=user.id, account_name=user.name)

    # Check URL creation limit
    rate_limiter = get_rate_limiter_service()
    can_create, current_count, limit = rate_limiter.can_create_url(db, str(account.id))

    if not can_create:
        limit_str = "unlimited" if limit is None else str(limit)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"URL creation limit reached: {current_count}/{limit_str} URLs. "
                "Please upgrade your plan to create more URLs."
            ),
        )

    # Create URL
    url_service = get_url_service(db)
    url = url_service.create_url(account_id=str(account.id))

    # Build response with path
    url_dict = {
        "id": str(url.id),
        "account_id": str(url.account_id),
        "unique_identifier": url.unique_identifier,
        "path": f"/webhooks/{url.unique_identifier}",
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "account": account,
    }
    return UrlResponse(**url_dict)


@router.get("", response_model=PaginatedResponse[UrlResponse])
async def get_urls(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max: 100)"),
    account_id: str = Query(None, description="Filter by account ID"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all URLs for the authenticated user with pagination.

    Args:
        page: Page number (default: 1, min: 1)
        page_size: Number of items per page (default: 10, max: 100)
        account_id: Optional account ID filter
        user: Current authenticated user
        db: Database session

    Returns:
        Paginated response with URLs

    Raises:
        HTTPException: 401 if not authenticated
    """
    url_service = get_url_service(db)
    account_service = get_account_service(db)

    # Get all user's accounts
    accounts = account_service.get_accounts(user.id)
    account_ids = [str(p.id) for p in accounts]

    # Filter by account_id if provided
    if account_id:
        if account_id not in account_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account with ID '{account_id}' not found",
            )
        account_ids = [account_id]

    # Get URLs for these accounts
    all_urls = []
    for pid in account_ids:
        urls = url_service.get_urls_by_account(pid)
        all_urls.extend(urls)

    # Pagination
    total_entries = len(all_urls)
    total_pages = (total_entries + page_size - 1) // page_size if total_entries > 0 else 1
    page = min(page, total_pages)
    skip = (page - 1) * page_size
    paginated_urls = all_urls[skip : skip + page_size]

    # Build responses
    url_responses = []
    for url in paginated_urls:
        account = account_service.get_account(str(url.account_id), user.id)
        url_dict = {
            "id": str(url.id),
            "account_id": str(url.account_id),
            "unique_identifier": url.unique_identifier,
            "path": f"/webhooks/{url.unique_identifier}",
            "created_at": url.created_at,
            "updated_at": url.updated_at,
            "account": account,
        }
        url_responses.append(UrlResponse(**url_dict))

    pagination_metadata = {
        "current_page": page,
        "total_pages": total_pages,
        "total_entries": total_entries,
        "page_size": page_size,
        "has_next": page < total_pages,
        "has_previous": page > 1,
        "next_page": page + 1 if page < total_pages else None,
        "previous_page": page - 1 if page > 1 else None,
    }

    return PaginatedResponse(
        data=url_responses,
        pagination=PaginationMetadata(**pagination_metadata),
    )


@router.get("/{url_id}", response_model=UrlResponse)
async def get_url(
    url_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a specific URL by ID.

    Args:
        url_id: ID of the URL to retrieve
        user: Current authenticated user
        db: Database session

    Returns:
        URL data

    Raises:
        HTTPException: 401 if not authenticated, 404 if URL not found
    """
    url_service = get_url_service(db)
    url = url_service.get_url(url_id)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with ID '{url_id}' not found",
        )

    # Verify user has access through account
    account_service = get_account_service(db)
    account = account_service.get_account(str(url.account_id), user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this URL",
        )

    url_dict = {
        "id": str(url.id),
        "account_id": str(url.account_id),
        "unique_identifier": url.unique_identifier,
        "path": f"/webhooks/{url.unique_identifier}",
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "account": account,
    }
    return UrlResponse(**url_dict)


@router.get("/{url_id}/logs", response_model=UrlWithLogsResponse)
async def get_url_logs(
    url_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page (max: 100)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all logs for a specific URL with pagination.

    Args:
        url_id: ID of the URL
        page: Page number (default: 1, min: 1)
        page_size: Number of items per page (default: 50, max: 100)
        user: Current authenticated user
        db: Database session

    Returns:
        URL data with logs

    Raises:
        HTTPException: 401 if not authenticated, 404 if URL not found
    """
    url_service = get_url_service(db)
    url = url_service.get_url(url_id)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with ID '{url_id}' not found",
        )

    # Verify user has access through account
    account_service = get_account_service(db)
    account = account_service.get_account(str(url.account_id), user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this URL",
        )

    # Get logs with pagination
    skip = (page - 1) * page_size
    logs = url_service.get_url_logs(url_id, limit=page_size, offset=skip)

    # Build log responses
    log_responses = [
        UrlLogResponse(
            id=str(log.id),
            url_id=str(log.url_id),
            method=str(log.method),
            headers=log.headers,
            query_params=log.query_params,
            body=log.body,
            response_status=log.response_status,
            response_headers=log.response_headers,
            response_body=log.response_body,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )
        for log in logs
    ]

    url_dict = {
        "id": str(url.id),
        "account_id": str(url.account_id),
        "unique_identifier": url.unique_identifier,
        "path": f"/webhooks/{url.unique_identifier}",
        "created_at": url.created_at,
        "updated_at": url.updated_at,
        "logs": log_responses,
    }
    return UrlWithLogsResponse(**url_dict)


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(
    url_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a URL.

    Args:
        url_id: ID of the URL to delete
        user: Current authenticated user
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException: 401 if not authenticated, 404 if URL not found
    """
    url_service = get_url_service(db)
    url = url_service.get_url(url_id)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with ID '{url_id}' not found",
        )

    # Verify user has access through account
    account_service = get_account_service(db)
    account = account_service.get_account(str(url.account_id), user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this URL",
        )

    deleted = url_service.delete_url(url_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with ID '{url_id}' not found",
        )

    return None
