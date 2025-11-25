"""API Key management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.users import current_active_user
from app.core.api_key import generate_api_key
from app.database.session import get_db
from app.models.users import User
from pydantic import BaseModel


router = APIRouter()


class APIKeyResponse(BaseModel):
    """Response model for API key generation."""
    api_key: str
    message: str


@router.post("/generate", response_model=APIKeyResponse)
async def generate_user_api_key(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Generate a new API key for the authenticated user.

    Requires JWT authentication. The generated API key will replace any existing one.

    Returns:
        APIKeyResponse with the new API key (only shown once!)
    """
    # Generate new API key
    new_api_key = generate_api_key()

    # Update user's API key
    current_user.api_key = new_api_key
    await session.commit()

    return APIKeyResponse(
        api_key=new_api_key,
        message="API key generated successfully. Store it securely - it won't be shown again!"
    )


@router.delete("/revoke")
async def revoke_api_key(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Revoke the current user's API key.

    Requires JWT authentication.

    Returns:
        Success message
    """
    current_user.api_key = None
    await session.commit()

    return {"message": "API key revoked successfully"}
