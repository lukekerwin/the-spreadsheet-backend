"""Stripe integration service for subscription management."""

from datetime import datetime, timezone
from typing import Optional
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.users import User

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
    async def get_or_create_customer(
        session: AsyncSession,
        user: User
    ) -> str:
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
            }
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
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        """Create a Stripe Checkout session for subscription.

        Args:
            session: Database session
            user: User object
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session URL
        """
        customer_id = await StripeService.get_or_create_customer(session, user)

        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=success_url or f"{FRONTEND_URL}/profile?subscription=success",
            cancel_url=cancel_url or f"{FRONTEND_URL}/profile?subscription=canceled",
            metadata={
                "user_id": str(user.id),
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user.id),
                },
            },
        )

        return checkout_session.url

    @staticmethod
    async def create_bidding_package_checkout(
        session: AsyncSession,
        user: User,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> str:
        """Create a Stripe Checkout session for bidding package one-time purchase.

        Args:
            session: Database session
            user: User object
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel

        Returns:
            Checkout session URL
        """
        customer_id = await StripeService.get_or_create_customer(session, user)

        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": STRIPE_BIDDING_PACKAGE_PRICE_ID,
                    "quantity": 1,
                },
            ],
            mode="payment",  # One-time payment, not subscription
            success_url=success_url or f"{FRONTEND_URL}/tools/bidding-package?purchase=success",
            cancel_url=cancel_url or f"{FRONTEND_URL}/tools/bidding-package?purchase=canceled",
            metadata={
                "user_id": str(user.id),
                "product_type": "bidding_package",
            },
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
        elif event_type == "invoice.payment_failed":
            await StripeService._handle_payment_failed(session, data)

        return {"status": "success", "event_type": event_type}

    @staticmethod
    async def _get_user_by_customer_id(
        session: AsyncSession,
        customer_id: str
    ) -> Optional[User]:
        """Get user by Stripe customer ID."""
        result = await session.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _handle_checkout_completed(
        session: AsyncSession,
        checkout_session: dict
    ) -> None:
        """Handle successful checkout completion."""
        customer_id = checkout_session.get("customer")
        subscription_id = checkout_session.get("subscription")
        metadata = checkout_session.get("metadata", {})
        mode = checkout_session.get("mode")

        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # Handle one-time payment for bidding package
        if mode == "payment" and metadata.get("product_type") == "bidding_package":
            user.has_bidding_package = True
            session.add(user)
            await session.commit()
            return

        # Handle subscription checkout
        if subscription_id:
            user.stripe_subscription_id = subscription_id

        session.add(user)
        await session.commit()

    @staticmethod
    async def _handle_subscription_created(
        session: AsyncSession,
        subscription: dict
    ) -> None:
        """Handle new subscription creation."""
        await StripeService._update_user_subscription(session, subscription)

    @staticmethod
    async def _handle_subscription_updated(
        session: AsyncSession,
        subscription: dict
    ) -> None:
        """Handle subscription updates (renewals, plan changes, etc.)."""
        await StripeService._update_user_subscription(session, subscription)

    @staticmethod
    async def _handle_subscription_deleted(
        session: AsyncSession,
        subscription: dict
    ) -> None:
        """Handle subscription cancellation."""
        customer_id = subscription.get("customer")
        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        # Reset subscription fields
        user.subscription_tier = "free"
        user.subscription_status = "canceled"
        user.stripe_subscription_id = None
        user.subscription_current_period_end = None
        user.subscription_cancel_at_period_end = False

        session.add(user)
        await session.commit()

    @staticmethod
    async def _handle_payment_failed(
        session: AsyncSession,
        invoice: dict
    ) -> None:
        """Handle failed payment."""
        customer_id = invoice.get("customer")
        if not customer_id:
            return

        user = await StripeService._get_user_by_customer_id(session, customer_id)
        if not user:
            return

        user.subscription_status = "past_due"
        session.add(user)
        await session.commit()

    @staticmethod
    async def _update_user_subscription(
        session: AsyncSession,
        subscription: dict
    ) -> None:
        """Update user subscription based on Stripe subscription object."""
        customer_id = subscription.get("customer")
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

        user.stripe_subscription_id = subscription.get("id")
        user.subscription_status = status_map.get(stripe_status, "none")

        # Set tier based on status
        if user.subscription_status in ("active", "trialing"):
            user.subscription_tier = "subscriber"
        else:
            user.subscription_tier = "free"

        # Set period end - prefer current_period_end, fall back to cancel_at if scheduled
        period_end = subscription.get("current_period_end")
        cancel_at = subscription.get("cancel_at")

        if period_end:
            user.subscription_current_period_end = datetime.fromtimestamp(
                period_end, tz=timezone.utc
            )
        elif cancel_at:
            # If no period_end but cancel_at exists, use that as the end date
            user.subscription_current_period_end = datetime.fromtimestamp(
                cancel_at, tz=timezone.utc
            )

        # Track if subscription is set to cancel - check both cancel_at_period_end and cancel_at
        user.subscription_cancel_at_period_end = (
            subscription.get("cancel_at_period_end", False) or cancel_at is not None
        )

        session.add(user)
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
        session: AsyncSession,
        user: User,
        at_period_end: bool = True
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

        if at_period_end:
            # Cancel at end of billing period
            stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=True
            )
            user.subscription_cancel_at_period_end = True
            # Status stays active until period ends
        else:
            # Cancel immediately
            stripe.Subscription.delete(user.stripe_subscription_id)
            user.subscription_tier = "free"
            user.subscription_status = "canceled"
            user.stripe_subscription_id = None
            user.subscription_cancel_at_period_end = False

        session.add(user)
        await session.commit()
        return True
