from datetime import datetime
from typing import TYPE_CHECKING

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base_class import Base

if TYPE_CHECKING:
    from app.models.subscriptions import Subscription, Purchase, PaymentHistory


class User(SQLAlchemyBaseUserTableUUID, Base):
    """User model for authentication.

    Inherits from SQLAlchemyBaseUserTableUUID which provides:
    - id: UUID primary key
    - email: str (unique, indexed)
    - hashed_password: str
    - is_active: bool (default True)
    - is_superuser: bool (default False)
    - is_verified: bool (default False)
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}  # Put in auth schema to separate from public

    # Additional custom fields
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    api_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)

    # Subscription fields
    subscription_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )  # 'free' or 'subscriber'
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none"
    )  # 'none', 'active', 'canceled', 'past_due', 'trialing'
    subscription_current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subscription_cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # One-time purchase access
    has_bidding_package: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # ========================================
    # Relationships to new subscription tables
    # ========================================
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user",
        lazy="selectin",
        order_by="desc(Subscription.created_at)",
    )
    purchases: Mapped[list["Purchase"]] = relationship(
        back_populates="user",
        lazy="selectin",
        order_by="desc(Purchase.created_at)",
    )
    payment_history: Mapped[list["PaymentHistory"]] = relationship(
        back_populates="user",
        lazy="dynamic",  # Use dynamic for potentially large collections
        order_by="desc(PaymentHistory.event_at)",
    )

    # ========================================
    # Computed Properties
    # ========================================

    @property
    def has_premium_access(self) -> bool:
        """Check if user has premium access.

        Checks both legacy fields and new subscription tables for backward compatibility.
        Superusers always have premium access.
        """
        if self.is_superuser:
            return True

        # Check new subscriptions table if relationships are loaded
        if self.subscriptions:
            for sub in self.subscriptions:
                if sub.status in ("active", "trialing"):
                    if sub.plan and sub.plan.features:
                        if sub.plan.features.get("premium_access"):
                            return True

        # Fallback to legacy fields
        if self.subscription_tier == "subscriber" and self.subscription_status in (
            "active",
            "trialing",
        ):
            return True

        return False

    @property
    def has_bidding_package_access(self) -> bool:
        """Check if user has purchased the bidding package.

        Checks both legacy field and new purchases table for backward compatibility.
        Superusers always have access.
        """
        if self.is_superuser:
            return True

        # Check new purchases table if relationships are loaded
        if self.purchases:
            for purchase in self.purchases:
                if purchase.status == "completed":
                    if purchase.plan and purchase.plan.features:
                        if purchase.plan.features.get("bidding_package"):
                            return True

        # Fallback to legacy field
        return self.has_bidding_package

    def get_active_subscriptions(self) -> list["Subscription"]:
        """Get all active subscriptions for this user."""
        return [s for s in self.subscriptions if s.status in ("active", "trialing")]

    def get_completed_purchases(self) -> list["Purchase"]:
        """Get all completed purchases for this user."""
        return [p for p in self.purchases if p.status == "completed"]
