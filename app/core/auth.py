"""Combined authentication (JWT + API Key)."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.users import current_active_user, fastapi_users
from app.core.api_key import get_user_from_api_key, api_key_header
from app.database.session import get_db
from app.models.users import User


# Create an optional user dependency for flexible auth
_optional_jwt_user = fastapi_users.current_user(active=True, optional=True)


async def get_current_user_flexible(
    session: AsyncSession = Depends(get_db),
    api_key: str | None = Depends(api_key_header),
    jwt_user: User | None = Depends(_optional_jwt_user),
) -> User:
    """Get current user from either JWT token or API key.

    Tries API key first, falls back to JWT.
    This allows endpoints to accept both authentication methods.

    Args:
        session: Database session
        api_key: API key from X-API-Key header (if present)
        jwt_user: User from JWT token (if present)

    Returns:
        Authenticated user

    Raises:
        HTTPException: 401 if neither auth method succeeds
    """
    # Try API key first
    if api_key:
        user = await get_user_from_api_key(api_key, session)
        if user:
            return user

    # Try JWT
    if jwt_user:
        return jwt_user

    # No valid auth
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Create an optional user dependency using fastapi_users
_optional_current_user = fastapi_users.current_user(active=True, optional=True)


async def get_current_user_optional(
    session: AsyncSession = Depends(get_db),
    api_key: str | None = Depends(api_key_header),
    jwt_user: User | None = Depends(_optional_current_user),
) -> User | None:
    """Get current user from either JWT token or API key, or return None.

    Tries API key first, falls back to JWT, returns None if neither present.
    This allows endpoints to work for both authenticated and unauthenticated users.

    Args:
        session: Database session
        api_key: API key from X-API-Key header (if present)
        jwt_user: User from JWT token (if present, None otherwise)

    Returns:
        Authenticated user or None
    """
    # Try API key first
    if api_key:
        user = await get_user_from_api_key(api_key, session)
        if user:
            return user

    # Try JWT
    if jwt_user:
        return jwt_user

    # No auth provided - this is OK for optional auth
    return None


async def get_premium_user(
    user: User = Depends(get_current_user_flexible),
) -> User:
    """Require authenticated user with premium access.

    First authenticates the user, then verifies they have premium access.
    Use this dependency for premium-only endpoints.

    Args:
        user: Authenticated user from get_current_user_flexible

    Returns:
        Authenticated premium user

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if authenticated but not premium
    """
    if not user.has_premium_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber access required to access this feature",
        )
    return user


async def get_bidding_package_user(
    user: User = Depends(get_current_user_flexible),
) -> User:
    """Require authenticated user with bidding package access.

    First authenticates the user, then verifies they own the bidding package.
    Use this dependency for bidding-package-only endpoints.

    Checks both the new purchases table and legacy has_bidding_package field
    for backward compatibility during migration.

    Args:
        user: Authenticated user from get_current_user_flexible

    Returns:
        Authenticated user with bidding package access

    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if authenticated but doesn't own bidding package
    """
    # Use the new property that checks both legacy field and new purchases table
    if not user.has_bidding_package_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bidding Package purchase required to access this feature",
        )
    return user


# Convenience aliases
require_auth = get_current_user_flexible
optional_auth = get_current_user_optional
require_premium = get_premium_user
require_bidding_package = get_bidding_package_user
