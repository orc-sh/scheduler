"""
Subscription controller for managing subscription operations with Chargebee.
Only exposes upgrade/downgrade and cancel operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.request.subscription_schemas import CancelSubscriptionRequest, UpdateSubscriptionRequest
from app.schemas.response.subscription_schemas import SubscriptionResponse
from app.services.project_service import get_project_service
from app.services.subscription_service import get_subscription_service
from db.client import client

router = APIRouter()


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update a subscription (upgrade/downgrade plan) via Chargebee.

    Args:
        subscription_id: ID of the subscription to update
        request: Subscription update request with new plan_id
        user: Current authenticated user
        db: Database session

    Returns:
        Updated subscription data

    Raises:
        HTTPException: 401 if not authenticated, 404 if subscription not found, 400 if update fails
    """
    try:
        subscription_service = get_subscription_service(db)
        subscription = subscription_service.get_subscription(subscription_id=subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID '{subscription_id}' not found",
            )

        # Verify user owns the project associated with this subscription
        project_service = get_project_service(db)
        project = project_service.get_project(project_id=subscription.project_id, user_id=user.id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this subscription",
            )

        # Update subscription
        updated_subscription = subscription_service.update_subscription(
            subscription_id=subscription_id,
            plan_id=request.plan_id,
        )

        if not updated_subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID '{subscription_id}' not found",
            )

        return SubscriptionResponse.from_model(updated_subscription)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}",
        )


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    subscription_id: str,
    request: CancelSubscriptionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Cancel a subscription via Chargebee.

    Args:
        subscription_id: ID of the subscription to cancel
        request: Cancellation request with optional reason
        user: Current authenticated user
        db: Database session

    Returns:
        Cancelled subscription data

    Raises:
        HTTPException: 401 if not authenticated, 404 if subscription not found, 400 if cancellation fails
    """
    try:
        subscription_service = get_subscription_service(db)
        subscription = subscription_service.get_subscription(subscription_id=subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID '{subscription_id}' not found",
            )

        # Verify user owns the project associated with this subscription
        project_service = get_project_service(db)
        project = project_service.get_project(project_id=subscription.project_id, user_id=user.id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this subscription",
            )

        # Cancel subscription
        cancelled_subscription = subscription_service.cancel_subscription(
            subscription_id=subscription_id,
            cancel_reason=request.cancel_reason,
        )

        if not cancelled_subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription with ID '{subscription_id}' not found",
            )

        return SubscriptionResponse.from_model(cancelled_subscription)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}",
        )
