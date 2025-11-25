"""API Key authentication utilities."""

import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.users import User

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


async def get_user_from_api_key(
    api_key: str | None = Security(api_key_header),
    session: AsyncSession = None
) -> User | None:
    """Validate API key and return user if valid.

    Args:
        api_key: API key from X-API-Key header
        session: Database session

    Returns:
        User if API key is valid, None otherwise
    """
    if not api_key:
        return None

    if not session:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session required"
        )

    # Look up user by API key
    statement = select(User).where(User.api_key == api_key, User.is_active == True)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()

    return user


async def require_api_key(
    api_key: str | None = Security(api_key_header),
    session: AsyncSession = None
) -> User:
    """Require valid API key, raise 401 if invalid.

    Args:
        api_key: API key from X-API-Key header
        session: Database session

    Returns:
        User object

    Raises:
        HTTPException: 401 if API key is invalid
    """
    user = await get_user_from_api_key(api_key, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return user
