"""User schemas for FastAPI-Users integration."""

import uuid
from datetime import datetime
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data."""
    first_name: str | None = None
    last_name: str | None = None
    # Subscription fields (read-only)
    subscription_tier: str = "free"
    subscription_status: str = "none"
    subscription_current_period_end: datetime | None = None
    has_premium_access: bool = False


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user."""
    first_name: str | None = None
    last_name: str | None = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating user data."""
    first_name: str | None = None
    last_name: str | None = None
