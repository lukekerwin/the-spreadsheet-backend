"""Subscription-related utilities for tier-based data access."""

from datetime import datetime, timezone
from typing import Optional

from app.models.users import User


def get_allowed_data_week(user: Optional[User], current_data_week: int) -> int:
    """Determine the maximum data week a user can access based on subscription.

    Business Logic:
    - Free users: Can only see data from the previous week (current_week - 1)
    - Premium users: Can see the latest data (current_week)
    - This implements the "Wednesday release" model where free users
      see the previous week's data until Wednesday when it becomes available.

    The data week is updated after each night's games (Sun/Mon/Tue).
    Free users see data released on Wednesday (which covers Sun-Tue games).
    Premium users see data immediately after each night's pipeline run.

    Args:
        user: The authenticated user (or None for unauthenticated)
        current_data_week: The current/latest data week in the database

    Returns:
        The maximum data_week_id the user is allowed to see
    """
    if user is None:
        # Unauthenticated users get free tier access
        return max(0, current_data_week - 1)

    if user.has_premium_access:
        # Premium users get full access to latest data
        return current_data_week

    # Free users get previous week's data
    return max(0, current_data_week - 1)


def is_data_release_day() -> bool:
    """Check if today is a data release day (Wednesday).

    On Wednesdays, free users get access to the previous week's data.
    This is when the "release" happens for free tier.

    Returns:
        True if today is Wednesday (data release day)
    """
    return datetime.now(timezone.utc).weekday() == 2  # Wednesday = 2


def get_subscription_message(user: Optional[User], current_week: int, user_week: int) -> Optional[str]:
    """Generate a message about data freshness for free users.

    Args:
        user: The authenticated user
        current_week: The latest data week available
        user_week: The data week the user can access

    Returns:
        A message to display to the user, or None if they have full access
    """
    if user is None or not user.has_premium_access:
        if current_week > user_week:
            weeks_behind = current_week - user_week
            return f"You're viewing data from {weeks_behind} week(s) ago. Subscribe for real-time updates after each game night."
    return None
