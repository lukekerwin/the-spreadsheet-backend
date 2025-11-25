"""Subscription management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_auth
from app.database.session import get_db
from app.models.users import User
from app.services.stripe_service import StripeService

router = APIRouter()


class CheckoutResponse(BaseModel):
    """Response for checkout session creation."""
    checkout_url: str


class PortalResponse(BaseModel):
    """Response for portal session creation."""
    portal_url: str


class SubscriptionStatus(BaseModel):
    """Current subscription status."""
    tier: str
    status: str
    current_period_end: str | None
    has_premium_access: bool


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(require_auth),
) -> SubscriptionStatus:
    """Get current user's subscription status."""
    return SubscriptionStatus(
        tier=current_user.subscription_tier,
        status=current_user.subscription_status,
        current_period_end=(
            current_user.subscription_current_period_end.isoformat()
            if current_user.subscription_current_period_end
            else None
        ),
        has_premium_access=current_user.has_premium_access,
    )


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for subscribing to premium.

    Returns a URL to redirect the user to for payment.
    """
    # Check if user already has an active subscription
    if current_user.subscription_status in ("active", "trialing"):
        raise HTTPException(
            status_code=400,
            detail="You already have an active subscription. Use the customer portal to manage it."
        )

    try:
        checkout_url = await StripeService.create_checkout_session(
            session=session,
            user=current_user,
        )
        return CheckoutResponse(checkout_url=checkout_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/create-portal", response_model=PortalResponse)
async def create_portal_session(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> PortalResponse:
    """Create a Stripe Customer Portal session for managing subscription.

    Returns a URL to redirect the user to for subscription management.
    """
    if not current_user.stripe_customer_id:
        raise HTTPException(
            status_code=400,
            detail="No subscription found. Please subscribe first."
        )

    try:
        portal_url = await StripeService.create_portal_session(
            session=session,
            user=current_user,
        )
        return PortalResponse(portal_url=portal_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Cancel the current user's subscription at the end of the billing period."""
    if not current_user.stripe_subscription_id:
        raise HTTPException(
            status_code=400,
            detail="No active subscription to cancel."
        )

    try:
        success = await StripeService.cancel_subscription(
            session=session,
            user=current_user,
            at_period_end=True,
        )
        if success:
            return {"message": "Subscription will be canceled at the end of the billing period."}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel subscription.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events.

    This endpoint is called by Stripe to notify us of subscription events.
    It must be publicly accessible (no auth) but verifies the webhook signature.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        result = await StripeService.handle_webhook_event(
            session=session,
            payload=payload,
            sig_header=sig_header,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Webhook processing failed: {str(e)}"
        )
