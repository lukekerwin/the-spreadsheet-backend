"""Stripe integration service for subscription management.

This service handles all Stripe operations and implements dual-write mode:
- Writes to legacy User model fields (for backward compatibility)
- Writes to new subscription/purchase tables (for new architecture)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.users import User
from app.models.subscriptions import Plan, Subscription, Purchase
from app.services.subscription_service import SubscriptionService

# Initialize Stripe with API key from settings
stripe.api_key = settings.STRIPE_SECRET_KEY

# Stripe configuration from settings
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_ID = settings.STRIPE_PRICE_ID
STRIPE_BIDDING_PACKAGE_PRICE_ID = settings.STRIPE_BIDDING_PACKAGE_PRICE_ID
FRONTEND_URL = settings.FRONTEND_URL


class StripeService:
    """Service for handling Stripe operations."""

    @staticmethod
    async def get_or_create_customer(session: AsyncSession, user: User) -> str:
        """Get existing Stripe customer or create a new one.

        Args:
            session: Database session
            user: User object

        Returns:
            Stripe customer ID
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id

        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
            metadata={
                "user_id": str(user.id),
            },
        )

        # Update user with customer ID
        user.stripe_customer_id = customer.id
        session.add(user)
        await session.commit()

        return customer.id

    @staticmethod
    async def create_checkout_session(
        session: AsyncSession,
        user: User,
        plan: Optional[Plan] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        """Create a Stripe Checkout session for subscription.

        Args:
            session: Database session
            user: User object
            plan: Plan object (optional, falls back to STRIPE_PRICE_ID)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session URL
        """
        customer_id = await StripeService.get_or_create_customer(session, user)

        # Use plan's price ID or fall back to config
        price_id = plan.stripe_price_id if plan else STRIPE_PRICE_ID
        plan_id = str(plan.id) if plan else None

        # Determine mode based on plan type
        mode = "subscription"
        if plan and plan.plan_type == "one_time":
            mode = "payment"

        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode=mode,
            success_url=success_url or f"{FRONTEND_URL}/profile?subscription=success",
            cancel_url=cancel_url or f"{FRONTEND_URL}/profile?subscription=canceled",
            metadata={
                "user_id": str(user.id),
                "plan_id": plan_id,
                "plan_type": plan.plan_type if plan else "subscription",
            },
            subscription_data=(
                {
                    "metadata": {
                        "user_id": str(user.id),
                        "plan_id": plan_id,
                    },
                }
                if mode == "subscription"
                else None
            ),
        )

        return checkout_session.url

    @staticmethod
    async def create_bidding_package_checkout(
        session: AsyncSession,
        user: User,
        plan: Optional[Plan] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        """Create a Stripe Checkout session for bidding package one-time purchase.

        Args:
            session: Database session
            user: User object
            plan: Plan object (optional, falls back to STRIPE_BIDDING_PACKAGE_PRICE_ID)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session URL
        """
        customer_id = await StripeService.get_or_create_customer(session, user)

        # Use plan's price ID or fall back to config
        price_id = plan.stripe_price_id if plan else STRIPE_BIDDING_PACKAGE_PRICE_ID
        plan_id = str(plan.id) if plan else None

        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="payment",  # One-time payment, not subscription
            success_url=success_url
            or f"{FRONTEND_URL}/tools/bidding-package?purchase=success",
            cancel_url=cancel_url
            or f"{FRONTEND_URL}/tools/bidding-package?purchase=canceled",
            metadata={
                "user_id": str(user.id),
                "plan_id": plan_id,
                "product_type": "bidding_package",
                "plan_type": "one_time",
            },
        )

        # Create pending purchase record in new table
        if plan:
            await SubscriptionService.create_purchase(
                session=session,
                user_id=user.id,
                plan_id=plan.id,
                amount_cents=plan.price_cents,
                stripe_checkout_session_id=checkout_session.id,
                status="pending",
            )

        return checkout_session.url

    @staticmethod
    async def create_portal_session(
        session: AsyncSession,
        user: User,
        return_url: Optional[str] = None,
    ) -> str:
        """Create a Stripe Customer Portal session for managing subscription.

        Args:
            session: Database session
            user: User object
            return_url: URL to return to after portal

        Returns:
            Portal session URL
        """
        if not user.stripe_customer_id:
            raise ValueError("User does not have a Stripe customer ID")

        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url or f"{FRONTEND_URL}/profile",
        )

        return portal_session.url

    @staticmethod
    async def handle_webhook_event(
        session: AsyncSession,
        payload: bytes,
        sig_header: str,
    ) -> dict:
        """Handle incoming Stripe webhook events.

        Args:
            session: Database session
            payload: Raw webhook payload
            sig_header: Stripe signature header

        Returns:
            Dict with processing result
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")

        # Handle the event
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            await StripeService._handle_checkout_completed(session, data)
        elif event_type == "customer.subscription.created":
            await StripeService._handle_subscription_created(session, data)
        elif event_type == "customer.subscription.updated":
            await StripeService._handle_subscription_updated(session, data)
        elif event_type == "customer.subscription.deleted":
            await StripeService._handle_subscription_deleted(session, data)
        elif event_type == "invoice.payment_succeeded":
            await StripeService._handle_invoice_paid(session, data)
        elif event_type == "invoice.payment_failed":
            await StripeService._handle_payment_failed(session, data)

        return {"status": "success", "event_type": event_type}

    @staticmethod
    async def _get_user_by_customer_id(
        session: AsyncSession, customer_id: str
    ) -> Optional[User]:
        """Get user by Stripe customer ID."""
        result = await session.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _handle_checkout_completed(
        session: AsyncSession, checkout_session: dict
    ) -> None:
        """Handle successful checkout completion."""
        customer_id = checkout_session.get("customer")
        subscription_id = checkout_session.get("subscription")
        metadata = checkout_session.get("metadata", {})
        mode = checkout_session.get("mode")
        checkout_session_id = checkout_session.get("id")
        plan_id = metadata.get("plan_id")

        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # Handle one-time payment for bidding package
        if mode == "payment" and metadata.get("product_type") == "bidding_package":
            # LEGACY: Update user model
            user.has_bidding_package = True
            session.add(user)

            # NEW: Complete the purchase in new table
            if plan_id:
                purchase = await SubscriptionService.get_purchase_by_checkout_session(
                    session, checkout_session_id
                )
                if purchase:
                    payment_intent_id = checkout_session.get("payment_intent")
                    await SubscriptionService.complete_purchase(
                        session, purchase, payment_intent_id
                    )

                    # Record payment history
                    await SubscriptionService.record_payment(
                        session=session,
                        user_id=user.id,
                        purchase_id=purchase.id,
                        event_type="payment_succeeded",
                        amount_cents=checkout_session.get(
                            "amount_total", purchase.amount_cents
                        ),
                        status="succeeded",
                        stripe_payment_intent_id=payment_intent_id,
                    )

            await session.commit()
            return

        # Handle subscription checkout
        if subscription_id:
            # LEGACY: Update user model
            user.stripe_subscription_id = subscription_id
            session.add(user)

        await session.commit()

    @staticmethod
    async def _handle_subscription_created(
        session: AsyncSession, subscription: dict
    ) -> None:
        """Handle new subscription creation."""
        await StripeService._update_user_subscription(session, subscription)

    @staticmethod
    async def _handle_subscription_updated(
        session: AsyncSession, subscription: dict
    ) -> None:
        """Handle subscription updates (renewals, plan changes, etc.)."""
        await StripeService._update_user_subscription(session, subscription)

    @staticmethod
    async def _handle_subscription_deleted(
        session: AsyncSession, subscription: dict
    ) -> None:
        """Handle subscription cancellation."""
        customer_id = subscription.get("customer")
        stripe_sub_id = subscription.get("id")

        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # LEGACY: Reset subscription fields on User
        user.subscription_tier = "free"
        user.subscription_status = "canceled"
        user.stripe_subscription_id = None
        user.subscription_current_period_end = None
        user.subscription_cancel_at_period_end = False
        session.add(user)

        # NEW: Update subscription in new table
        if stripe_sub_id:
            sub = await SubscriptionService.get_subscription_by_stripe_id(
                session, stripe_sub_id
            )
            if sub:
                await SubscriptionService.update_subscription_status(
                    session=session,
                    subscription=sub,
                    status="canceled",
                    ended_at=datetime.now(timezone.utc),
                )

        await session.commit()

    @staticmethod
    async def _handle_invoice_paid(session: AsyncSession, invoice: dict) -> None:
        """Handle successful invoice payment."""
        customer_id = invoice.get("customer")
        stripe_sub_id = invoice.get("subscription")

        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # Find subscription in new table
        subscription = None
        if stripe_sub_id:
            subscription = await SubscriptionService.get_subscription_by_stripe_id(
                session, stripe_sub_id
            )

        # Record payment history
        await SubscriptionService.record_payment(
            session=session,
            user_id=user.id,
            subscription_id=subscription.id if subscription else None,
            event_type="payment_succeeded",
            amount_cents=invoice.get("amount_paid", 0),
            status="succeeded",
            stripe_invoice_id=invoice.get("id"),
            stripe_payment_intent_id=invoice.get("payment_intent"),
            invoice_url=invoice.get("hosted_invoice_url"),
            receipt_url=invoice.get("invoice_pdf"),
        )

    @staticmethod
    async def _handle_payment_failed(session: AsyncSession, invoice: dict) -> None:
        """Handle failed payment."""
        customer_id = invoice.get("customer")
        stripe_sub_id = invoice.get("subscription")

        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # LEGACY: Update user status
        user.subscription_status = "past_due"
        session.add(user)

        # NEW: Update subscription in new table
        subscription = None
        if stripe_sub_id:
            subscription = await SubscriptionService.get_subscription_by_stripe_id(
                session, stripe_sub_id
            )
            if subscription:
                await SubscriptionService.update_subscription_status(
                    session=session,
                    subscription=subscription,
                    status="past_due",
                )

        # Record payment history
        failure_message = None
        if invoice.get("last_finalization_error"):
            failure_message = invoice["last_finalization_error"].get("message")

        await SubscriptionService.record_payment(
            session=session,
            user_id=user.id,
            subscription_id=subscription.id if subscription else None,
            event_type="payment_failed",
            amount_cents=invoice.get("amount_due", 0),
            status="failed",
            stripe_invoice_id=invoice.get("id"),
            failure_reason=failure_message,
        )

        await session.commit()

    @staticmethod
    async def _update_user_subscription(
        session: AsyncSession, subscription: dict
    ) -> None:
        """Update user subscription based on Stripe subscription object.

        Implements dual-write: updates both legacy User fields and new Subscription table.
        """
        customer_id = subscription.get("customer")
        stripe_sub_id = subscription.get("id")

        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # Map Stripe status to our status
        stripe_status = subscription.get("status")
        status_map = {
            "active": "active",
            "trialing": "trialing",
            "past_due": "past_due",
            "canceled": "canceled",
            "unpaid": "past_due",
            "incomplete": "none",
            "incomplete_expired": "none",
        }
        mapped_status = status_map.get(stripe_status, "none")

        # Parse timestamps
        period_start = subscription.get("current_period_start")
        period_end = subscription.get("current_period_end")
        cancel_at = subscription.get("cancel_at")
        trial_start = subscription.get("trial_start")
        trial_end = subscription.get("trial_end")

        period_start_dt = (
            datetime.fromtimestamp(period_start, tz=timezone.utc)
            if period_start
            else None
        )
        period_end_dt = (
            datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None
        )
        trial_start_dt = (
            datetime.fromtimestamp(trial_start, tz=timezone.utc)
            if trial_start
            else None
        )
        trial_end_dt = (
            datetime.fromtimestamp(trial_end, tz=timezone.utc) if trial_end else None
        )

        cancel_at_period_end = subscription.get("cancel_at_period_end", False) or (
            cancel_at is not None
        )

        # ============================================
        # LEGACY: Update User model fields
        # ============================================
        user.stripe_subscription_id = stripe_sub_id
        user.subscription_status = mapped_status

        # Set tier based on status
        if mapped_status in ("active", "trialing"):
            user.subscription_tier = "subscriber"
        else:
            user.subscription_tier = "free"

        # Set period end
        if period_end_dt:
            user.subscription_current_period_end = period_end_dt
        elif cancel_at:
            user.subscription_current_period_end = datetime.fromtimestamp(
                cancel_at, tz=timezone.utc
            )

        user.subscription_cancel_at_period_end = cancel_at_period_end
        session.add(user)

        # ============================================
        # NEW: Update Subscription table
        # ============================================
        # Get price ID from subscription items
        items = subscription.get("items", {}).get("data", [])
        stripe_price_id = items[0]["price"]["id"] if items else None

        # Look up plan by price ID
        plan = None
        if stripe_price_id:
            plan = await SubscriptionService.get_plan_by_stripe_price_id(
                session, stripe_price_id
            )

        if plan:
            # Check if subscription record exists
            sub = await SubscriptionService.get_subscription_by_stripe_id(
                session, stripe_sub_id
            )

            if sub:
                # Update existing subscription
                await SubscriptionService.update_subscription_status(
                    session=session,
                    subscription=sub,
                    status=mapped_status,
                    current_period_start=period_start_dt,
                    current_period_end=period_end_dt,
                    cancel_at_period_end=cancel_at_period_end,
                )
            else:
                # Create new subscription record
                await SubscriptionService.create_subscription(
                    session=session,
                    user_id=user.id,
                    plan_id=plan.id,
                    stripe_subscription_id=stripe_sub_id,
                    status=mapped_status,
                    current_period_start=period_start_dt,
                    current_period_end=period_end_dt,
                    trial_start=trial_start_dt,
                    trial_end=trial_end_dt,
                )

        await session.commit()

    @staticmethod
    async def sync_subscription_from_stripe(
        session: AsyncSession,
        user: User,
    ) -> bool:
        """Sync user's subscription data from Stripe.

        Args:
            session: Database session
            user: User object

        Returns:
            True if subscription was synced
        """
        if not user.stripe_subscription_id:
            return False

        try:
            subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            await StripeService._update_user_subscription(session, subscription)
            return True
        except stripe.error.StripeError:
            return False

    @staticmethod
    async def cancel_subscription(
        session: AsyncSession, user: User, at_period_end: bool = True
    ) -> bool:
        """Cancel a user's subscription.

        Args:
            session: Database session
            user: User object
            at_period_end: If True, cancel at end of period. If False, cancel immediately.

        Returns:
            True if successful
        """
        if not user.stripe_subscription_id:
            return False

        stripe_sub_id = user.stripe_subscription_id

        if at_period_end:
            # Cancel at end of billing period
            stripe.Subscription.modify(stripe_sub_id, cancel_at_period_end=True)

            # LEGACY: Update user
            user.subscription_cancel_at_period_end = True
            session.add(user)

            # NEW: Update subscription table
            sub = await SubscriptionService.get_subscription_by_stripe_id(
                session, stripe_sub_id
            )
            if sub:
                await SubscriptionService.update_subscription_status(
                    session=session,
                    subscription=sub,
                    status=sub.status,  # Keep current status
                    cancel_at_period_end=True,
                    canceled_at=datetime.now(timezone.utc),
                )
        else:
            # Cancel immediately
            stripe.Subscription.delete(stripe_sub_id)

            # LEGACY: Update user
            user.subscription_tier = "free"
            user.subscription_status = "canceled"
            user.stripe_subscription_id = None
            user.subscription_cancel_at_period_end = False
            session.add(user)

            # NEW: Update subscription table
            sub = await SubscriptionService.get_subscription_by_stripe_id(
                session, stripe_sub_id
            )
            if sub:
                await SubscriptionService.update_subscription_status(
                    session=session,
                    subscription=sub,
                    status="canceled",
                    ended_at=datetime.now(timezone.utc),
                )

        await session.commit()
        return True
