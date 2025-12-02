"""
Subscription controller for managing subscription operations with Chargebee.
Exposes upgrade/downgrade, cancel operations and helpers for hosted-page flows.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.clients.subscription_client import get_subscription_client
from app.constants.app_constants import BACKEND_BASE_URL, FRONTEND_BASE_URL
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.response.subscription_schemas import SubscriptionResponse
from app.services.subscription_service import get_subscription_service
from db.client import client

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateUpgradeUrlRequest(BaseModel):
    """Request body for creating a Chargebee upgrade/checkout URL."""

    plan_id: str


class UpgradeUrlResponse(BaseModel):
    """Response containing the URL to redirect the customer to."""

    url: str


class SyncFromChargebeeRequest(BaseModel):
    """Request body for syncing subscription after hosted-page redirect."""

    hosted_page_id: str


@router.get("", response_model=list[SubscriptionResponse])
async def get_subscriptions(
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all subscriptions for the authenticated user.

    Args:
        user: Current authenticated user
        db: Database session

    Returns:
        List of subscription data for the user

    Raises:
        HTTPException: 401 if not authenticated
    """
    try:
        subscription_service = get_subscription_service(db)
        subscriptions = subscription_service.get_subscriptions_by_user(user_id=user.id)

        return [SubscriptionResponse.from_model(sub) for sub in subscriptions]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscriptions: {str(e)}",
        )


@router.post("/upgrade", response_model=UpgradeUrlResponse)
async def create_upgrade_url(
    body: CreateUpgradeUrlRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a Chargebee hosted-page URL to upgrade/downgrade a subscription.

    This endpoint returns a URL that the frontend can redirect the user to.
    After payment is completed, Chargebee should redirect back to `callback_url`
    with the hosted_page_id, and the frontend can then call the sync endpoint.
    """
    try:
        subscription_service = get_subscription_service(db)
        subscriptions = subscription_service.get_subscriptions_by_user(user_id=user.id)

        if not subscriptions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No subscription found for this user.",
            )

        # Prefer the first subscription (you already ensure single-subscription-per-account)
        subscription = subscriptions[0]

        cb_client = get_subscription_client()

        # Backend callback URL that Chargebee will redirect to after checkout.
        # This endpoint will sync the subscription and then redirect the browser to the frontend.
        backend_callback = f"{BACKEND_BASE_URL}/api/subscriptions/callback"

        # Use Chargebee Hosted Page checkout for existing subscription (Product Catalog 2.0 compatible)
        # This creates a checkout page where the customer can update card details and change plans.
        # After completion, Chargebee redirects back to backend_callback with hosted_page_id.
        hosted_page_cls = cb_client._client.HostedPage  # type: ignore[attr-defined]

        params = {
            "subscription": {
                "id": str(subscription.chargebee_subscription_id),
            },
            "subscription_items": [
                {
                    "item_price_id": body.plan_id,
                    "quantity": 1,
                }
            ],
            "redirect_url": backend_callback,
            "cancel_url": backend_callback,
        }
        hosted_page = hosted_page_cls.checkout_existing_for_items(params)  # type: ignore[arg-type]
        checkout_url = str(hosted_page.hosted_page.url)

        return UpgradeUrlResponse(url=checkout_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create upgrade URL: {str(e)}",
        )


@router.get("/callback")
async def chargebee_callback(request: Request, db: Session = Depends(client)) -> Response:
    """
    Backend callback endpoint for Chargebee hosted checkout.

    Chargebee redirects the browser here after checkout with a hosted_page_id query param.
    This endpoint:
      1. Retrieves the hosted page and subscription from Chargebee.
      2. Syncs the subscription to the local database.
      3. Redirects the user to the frontend (Profile page by default).
    """
    hosted_page_id = request.query_params.get("id")

    if not hosted_page_id:
        # Missing hosted_page_id, just send user to frontend with an error flag
        redirect_url = f"{FRONTEND_BASE_URL or ''}/profile?billing_error=missing_hosted_page_id"
        return Response(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": redirect_url})

    try:
        cb_client = get_subscription_client()
        hosted_page = cb_client._client.HostedPage.retrieve(hosted_page_id)  # type: ignore[attr-defined]

        # Chargebee 3.x HostedPage structure can differ; try multiple ways to get subscription id
        hp = hosted_page.hosted_page  # type: ignore[attr-defined]

        cb_subscription = getattr(hp, "subscription", None)
        subscription_id = None

        if cb_subscription is not None and getattr(cb_subscription, "id", None):
            subscription_id = str(cb_subscription.id)  # type: ignore[attr-defined]
        else:
            # Fallback: some PC 2.0 flows put subscription under hosted page content
            content = getattr(hp, "content", None)
            if content is not None:
                # content might be an object or dict-like
                sub_from_content = getattr(content, "subscription", None)
                if sub_from_content is None and isinstance(content, dict):
                    sub_from_content = content.get("subscription")

                if sub_from_content is not None:
                    if isinstance(sub_from_content, dict):
                        subscription_id = str(sub_from_content.get("id"))
                    elif getattr(sub_from_content, "id", None):
                        subscription_id = str(sub_from_content.id)  # type: ignore[attr-defined]

        if not subscription_id:
            redirect_url = f"{FRONTEND_BASE_URL or ''}/profile?billing_error=sub_missing_from_hosted_page"
            return Response(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": redirect_url},
            )

        subscription_service = get_subscription_service(db)
        updated_subscription = subscription_service.sync_subscription_from_chargebee(subscription_id)

        if not updated_subscription:
            redirect_url = f"{FRONTEND_BASE_URL or ''}/profile?billing_error=sub_not_found"
            return Response(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": redirect_url})

        # Success: redirect to frontend profile with success flag
        redirect_url = f"{FRONTEND_BASE_URL or ''}/profile?billing_success=1"
        return Response(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": redirect_url})
    except Exception as e:
        logger.error(f"Failed to sync subscription from Chargebee: {str(e)}")
        redirect_url = f"{FRONTEND_BASE_URL or ''}/profile?billing_error=sync_failed"
        return Response(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": redirect_url})
