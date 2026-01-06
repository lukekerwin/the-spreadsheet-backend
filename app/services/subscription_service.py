"""Subscription management service.

Provides CRUD operations for plans, subscriptions, purchases, and payment history.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscriptions import Plan, Subscription, Purchase, PaymentHistory


class SubscriptionService:
    """Service for managing subscriptions and purchases."""

    # ========================================
    # PLAN OPERATIONS
    # ========================================

    @staticmethod
    async def get_plan_by_id(
        session: AsyncSession,
        plan_id: UUID,
    ) -> Optional[Plan]:
        """Get plan by ID."""
        result = await session.execute(select(Plan).where(Plan.id == plan_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_plan_by_stripe_price_id(
        session: AsyncSession,
        stripe_price_id: str,
    ) -> Optional[Plan]:
        """Get plan by Stripe price ID."""
        result = await session.execute(
            select(Plan).where(Plan.stripe_price_id == stripe_price_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_plans(
        session: AsyncSession,
        plan_type: Optional[str] = None,
    ) -> list[Plan]:
        """Get all active plans, optionally filtered by type."""
        query = select(Plan).where(Plan.is_active == True).order_by(Plan.sort_order)
        if plan_type:
            query = query.where(Plan.plan_type == plan_type)
        result = await session.execute(query)
        return list(result.scalars().all())

    # ========================================
    # SUBSCRIPTION OPERATIONS
    # ========================================

    @staticmethod
    async def get_subscription_by_id(
        session: AsyncSession,
        subscription_id: UUID,
    ) -> Optional[Subscription]:
        """Get subscription by ID with plan loaded."""
        result = await session.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_subscription_by_stripe_id(
        session: AsyncSession,
        stripe_subscription_id: str,
    ) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID with relationships loaded."""
        result = await session.execute(
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.user),
            )
            .where(Subscription.stripe_subscription_id == stripe_subscription_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_subscriptions(
        session: AsyncSession,
        user_id: UUID,
        active_only: bool = False,
    ) -> list[Subscription]:
        """Get all subscriptions for a user."""
        query = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        if active_only:
            query = query.where(Subscription.status.in_(["active", "trialing"]))
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_active_subscription(
        session: AsyncSession,
        user_id: UUID,
        plan_id: Optional[UUID] = None,
    ) -> Optional[Subscription]:
        """Get user's active subscription, optionally filtered by plan."""
        query = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        if plan_id:
            query = query.where(Subscription.plan_id == plan_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_subscription(
        session: AsyncSession,
        user_id: UUID,
        plan_id: UUID,
        stripe_subscription_id: Optional[str] = None,
        status: str = "pending",
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        trial_start: Optional[datetime] = None,
        trial_end: Optional[datetime] = None,
    ) -> Subscription:
        """Create a new subscription record."""
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            trial_start=trial_start,
            trial_end=trial_end,
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    @staticmethod
    async def update_subscription_status(
        session: AsyncSession,
        subscription: Subscription,
        status: str,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        cancel_at_period_end: Optional[bool] = None,
        canceled_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
    ) -> Subscription:
        """Update subscription status and related fields."""
        subscription.status = status
        subscription.updated_at = datetime.now(timezone.utc)

        if current_period_start is not None:
            subscription.current_period_start = current_period_start
        if current_period_end is not None:
            subscription.current_period_end = current_period_end
        if cancel_at_period_end is not None:
            subscription.cancel_at_period_end = cancel_at_period_end
        if canceled_at is not None:
            subscription.canceled_at = canceled_at
        if ended_at is not None:
            subscription.ended_at = ended_at

        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    # ========================================
    # PURCHASE OPERATIONS
    # ========================================

    @staticmethod
    async def get_purchase_by_id(
        session: AsyncSession,
        purchase_id: UUID,
    ) -> Optional[Purchase]:
        """Get purchase by ID with plan loaded."""
        result = await session.execute(
            select(Purchase)
            .options(selectinload(Purchase.plan))
            .where(Purchase.id == purchase_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_purchases(
        session: AsyncSession,
        user_id: UUID,
        completed_only: bool = False,
    ) -> list[Purchase]:
        """Get all purchases for a user."""
        query = (
            select(Purchase)
            .options(selectinload(Purchase.plan))
            .where(Purchase.user_id == user_id)
            .order_by(Purchase.created_at.desc())
        )
        if completed_only:
            query = query.where(Purchase.status == "completed")
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_purchase(
        session: AsyncSession,
        user_id: UUID,
        plan_id: UUID,
    ) -> Optional[Purchase]:
        """Get user's purchase for a specific plan."""
        result = await session.execute(
            select(Purchase)
            .options(selectinload(Purchase.plan))
            .where(
                Purchase.user_id == user_id,
                Purchase.plan_id == plan_id,
                Purchase.status == "completed",
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_purchase_by_checkout_session(
        session: AsyncSession,
        checkout_session_id: str,
    ) -> Optional[Purchase]:
        """Get purchase by Stripe checkout session ID."""
        result = await session.execute(
            select(Purchase)
            .options(selectinload(Purchase.plan), selectinload(Purchase.user))
            .where(Purchase.stripe_checkout_session_id == checkout_session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_purchase(
        session: AsyncSession,
        user_id: UUID,
        plan_id: UUID,
        amount_cents: int,
        stripe_payment_intent_id: Optional[str] = None,
        stripe_checkout_session_id: Optional[str] = None,
        status: str = "pending",
        currency: str = "usd",
    ) -> Purchase:
        """Create a new purchase record."""
        purchase = Purchase(
            user_id=user_id,
            plan_id=plan_id,
            amount_cents=amount_cents,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_checkout_session_id=stripe_checkout_session_id,
            status=status,
            currency=currency,
        )
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)
        return purchase

    @staticmethod
    async def complete_purchase(
        session: AsyncSession,
        purchase: Purchase,
        stripe_payment_intent_id: Optional[str] = None,
    ) -> Purchase:
        """Mark purchase as completed."""
        purchase.status = "completed"
        purchase.purchased_at = datetime.now(timezone.utc)
        purchase.updated_at = datetime.now(timezone.utc)
        if stripe_payment_intent_id:
            purchase.stripe_payment_intent_id = stripe_payment_intent_id
        session.add(purchase)
        await session.commit()
        await session.refresh(purchase)
        return purchase

    # ========================================
    # PAYMENT HISTORY OPERATIONS
    # ========================================

    @staticmethod
    async def get_user_payment_history(
        session: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PaymentHistory]:
        """Get payment history for a user."""
        result = await session.execute(
            select(PaymentHistory)
            .where(PaymentHistory.user_id == user_id)
            .order_by(PaymentHistory.event_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def record_payment(
        session: AsyncSession,
        user_id: UUID,
        event_type: str,
        amount_cents: int,
        status: str,
        subscription_id: Optional[UUID] = None,
        purchase_id: Optional[UUID] = None,
        stripe_invoice_id: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None,
        stripe_charge_id: Optional[str] = None,
        invoice_url: Optional[str] = None,
        receipt_url: Optional[str] = None,
        failure_reason: Optional[str] = None,
        refund_reason: Optional[str] = None,
        currency: str = "usd",
    ) -> PaymentHistory:
        """Record a payment event."""
        payment = PaymentHistory(
            user_id=user_id,
            subscription_id=subscription_id,
            purchase_id=purchase_id,
            event_type=event_type,
            amount_cents=amount_cents,
            status=status,
            stripe_invoice_id=stripe_invoice_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            stripe_charge_id=stripe_charge_id,
            invoice_url=invoice_url,
            receipt_url=receipt_url,
            failure_reason=failure_reason,
            refund_reason=refund_reason,
            currency=currency,
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment

    # ========================================
    # FEATURE ACCESS CHECKS
    # ========================================

    @staticmethod
    async def user_has_feature(
        session: AsyncSession,
        user_id: UUID,
        feature_key: str,
    ) -> bool:
        """Check if user has access to a specific feature.

        Checks both active subscriptions and completed purchases.
        """
        # Check active subscriptions
        sub_result = await session.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.user_id == user_id,
                Subscription.status.in_(["active", "trialing"]),
            )
        )
        for sub in sub_result.scalars():
            if sub.plan.features and sub.plan.features.get(feature_key):
                return True

        # Check completed purchases
        purchase_result = await session.execute(
            select(Purchase)
            .options(selectinload(Purchase.plan))
            .where(
                Purchase.user_id == user_id,
                Purchase.status == "completed",
            )
        )
        for purchase in purchase_result.scalars():
            if purchase.plan.features and purchase.plan.features.get(feature_key):
                return True

        return False

    @staticmethod
    async def user_has_premium_access(
        session: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """Check if user has premium access via subscription."""
        return await SubscriptionService.user_has_feature(
            session, user_id, "premium_access"
        )

    @staticmethod
    async def user_has_bidding_package(
        session: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """Check if user has purchased the bidding package."""
        return await SubscriptionService.user_has_feature(
            session, user_id, "bidding_package"
        )
