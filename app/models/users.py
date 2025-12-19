from datetime import datetime

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


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

    @property
    def has_premium_access(self) -> bool:
        """Check if user has premium access (either premium tier or superuser)."""
        if self.is_superuser:
            return True
        if self.subscription_tier == "subscriber" and self.subscription_status in ("active", "trialing"):
            return True
        return False
