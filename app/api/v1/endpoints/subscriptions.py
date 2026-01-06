"""Subscription management endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import require_auth
from app.database.session import get_db
from app.models.users import User
from app.models.subscriptions import Plan, Subscription, Purchase, PaymentHistory
from app.services.stripe_service import StripeService
from app.services.subscription_service import SubscriptionService

router = APIRouter()


# ========================================
# SCHEMAS
# ========================================


class CheckoutResponse(BaseModel):
    """Response for checkout session creation."""

    checkout_url: str


class CheckoutRequest(BaseModel):
    """Request for checkout session creation with plan."""

    plan_id: Optional[UUID] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PortalResponse(BaseModel):
    """Response for portal session creation."""

    portal_url: str


class PlanResponse(BaseModel):
    """Plan information."""

    id: UUID
    name: str
    description: Optional[str]
    plan_type: str
    billing_interval: Optional[str]
    price_cents: int
    currency: str
    features: Optional[dict]

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription information."""

    id: UUID
    plan: PlanResponse
    status: str
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseResponse(BaseModel):
    """Purchase information."""

    id: UUID
    plan: PlanResponse
    status: str
    amount_cents: int
    currency: str
    purchased_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionStatus(BaseModel):
    """Current subscription status with backward compatibility."""

    # Legacy fields for backward compatibility
    tier: str
    status: str
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    has_premium_access: bool
    has_bidding_package: bool

    # New detailed fields
    subscriptions: list[SubscriptionResponse]
    purchases: list[PurchaseResponse]


class PaymentHistoryResponse(BaseModel):
    """Payment history entry."""

    id: UUID
    event_type: str
    amount_cents: int
    currency: str
    status: str
    invoice_url: Optional[str]
    receipt_url: Optional[str]
    event_at: datetime

    class Config:
        from_attributes = True


# ========================================
# ENDPOINTS
# ========================================


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    plan_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> list[PlanResponse]:
    """List available subscription plans.

    Args:
        plan_type: Filter by plan type ('subscription' or 'one_time')
    """
    plans = await SubscriptionService.get_active_plans(session, plan_type)
    return [PlanResponse.model_validate(p) for p in plans]


@router.get("/status", response_model=SubscriptionStatus)
async def get_subscription_status(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> SubscriptionStatus:
    """Get current user's subscription status.

    Returns both legacy fields (for backward compatibility) and
    new detailed subscription/purchase arrays.
    """
    # Load user with subscriptions and purchases
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.subscriptions).selectinload(Subscription.plan),
            selectinload(User.purchases).selectinload(Purchase.plan),
        )
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()

    # Build legacy compatibility fields
    active_sub = next(
        (s for s in user.subscriptions if s.status in ("active", "trialing")),
        None,
    )

    tier = "subscriber" if active_sub else user.subscription_tier
    status = active_sub.status if active_sub else user.subscription_status
    period_end = None
    if active_sub and active_sub.current_period_end:
        period_end = active_sub.current_period_end.isoformat()
    elif user.subscription_current_period_end:
        period_end = user.subscription_current_period_end.isoformat()

    cancel_at_period_end = (
        active_sub.cancel_at_period_end
        if active_sub
        else user.subscription_cancel_at_period_end
    )

    return SubscriptionStatus(
        tier=tier,
        status=status,
        current_period_end=period_end,
        cancel_at_period_end=cancel_at_period_end,
        has_premium_access=user.has_premium_access,
        has_bidding_package=user.has_bidding_package_access,
        subscriptions=[
            SubscriptionResponse(
                id=s.id,
                plan=PlanResponse.model_validate(s.plan),
                status=s.status,
                current_period_start=s.current_period_start,
                current_period_end=s.current_period_end,
                cancel_at_period_end=s.cancel_at_period_end,
                canceled_at=s.canceled_at,
                created_at=s.created_at,
            )
            for s in user.subscriptions
        ],
        purchases=[
            PurchaseResponse(
                id=p.id,
                plan=PlanResponse.model_validate(p.plan),
                status=p.status,
                amount_cents=p.amount_cents,
                currency=p.currency,
                purchased_at=p.purchased_at,
                created_at=p.created_at,
            )
            for p in user.purchases
            if p.status == "completed"
        ],
    )


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: Optional[CheckoutRequest] = None,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for subscribing to premium.

    Args:
        request: Optional request body with plan_id, success_url, cancel_url

    Returns a URL to redirect the user to for payment.
    """
    plan = None
    success_url = None
    cancel_url = None

    if request:
        success_url = request.success_url
        cancel_url = request.cancel_url
        if request.plan_id:
            plan = await SubscriptionService.get_plan_by_id(session, request.plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")

    # Check if user already has an active subscription for this plan
    if plan:
        existing = await SubscriptionService.get_active_subscription(
            session, current_user.id, plan.id
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="You already have an active subscription for this plan.",
            )
    else:
        # Legacy check
        if current_user.subscription_status in ("active", "trialing"):
            raise HTTPException(
                status_code=400,
                detail="You already have an active subscription. Use the customer portal to manage it.",
            )

    try:
        checkout_url = await StripeService.create_checkout_session(
            session=session,
            user=current_user,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return CheckoutResponse(checkout_url=checkout_url)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create checkout session: {str(e)}"
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
            status_code=400, detail="No subscription found. Please subscribe first."
        )

    try:
        portal_url = await StripeService.create_portal_session(
            session=session,
            user=current_user,
        )
        return PortalResponse(portal_url=portal_url)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/purchase-bidding-package", response_model=CheckoutResponse)
async def purchase_bidding_package(
    request: Optional[CheckoutRequest] = None,
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    """Create a Stripe Checkout session for purchasing the Bidding Package.

    This is a one-time payment, not a subscription.
    Returns a URL to redirect the user to for payment.
    """
    plan = None
    success_url = None
    cancel_url = None

    if request:
        success_url = request.success_url
        cancel_url = request.cancel_url
        if request.plan_id:
            plan = await SubscriptionService.get_plan_by_id(session, request.plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")

    # Check if user already owns the bidding package
    if current_user.has_bidding_package_access:
        raise HTTPException(status_code=400, detail="You already own the Bidding Package.")

    # If plan specified, check for existing purchase
    if plan:
        existing = await SubscriptionService.get_purchase(
            session, current_user.id, plan.id
        )
        if existing:
            raise HTTPException(
                status_code=400, detail="You already own this product."
            )

    try:
        checkout_url = await StripeService.create_bidding_package_checkout(
            session=session,
            user=current_user,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return CheckoutResponse(checkout_url=checkout_url)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/history", response_model=list[PaymentHistoryResponse])
async def get_payment_history(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0),
) -> list[PaymentHistoryResponse]:
    """Get current user's payment history.

    Returns a list of payment events ordered by date (most recent first).
    """
    payments = await SubscriptionService.get_user_payment_history(
        session, current_user.id, limit, offset
    )
    return [PaymentHistoryResponse.model_validate(p) for p in payments]


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Cancel the current user's subscription at the end of the billing period."""
    if not current_user.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription to cancel.")

    try:
        success = await StripeService.cancel_subscription(
            session=session,
            user=current_user,
            at_period_end=True,
        )
        if success:
            return {
                "message": "Subscription will be canceled at the end of the billing period."
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel subscription.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/sync")
async def sync_subscription(
    current_user: User = Depends(require_auth),
    session: AsyncSession = Depends(get_db),
):
    """Sync subscription data from Stripe.

    This refreshes the local subscription data with the latest from Stripe.
    """
    if not current_user.stripe_subscription_id:
        raise HTTPException(status_code=400, detail="No subscription to sync.")

    try:
        success = await StripeService.sync_subscription_from_stripe(
            session=session,
            user=current_user,
        )
        if success:
            return {"message": "Subscription synced successfully."}
        else:
            raise HTTPException(status_code=400, detail="Failed to sync subscription.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to sync subscription: {str(e)}"
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
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )
