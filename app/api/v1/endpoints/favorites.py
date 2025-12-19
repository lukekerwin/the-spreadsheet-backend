"""
Favorites Endpoints

Endpoints for managing user favorites (bidding package players).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database.session import get_db
from app.models.users import User
from app.core.auth import require_auth

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter()

# ============================================
# SCHEMAS
# ============================================

class FavoriteResponse(BaseModel):
    signup_id: str
    is_favorite: bool

class FavoritesList(BaseModel):
    favorites: list[str]

# ============================================
# ENDPOINTS
# ============================================

@router.get("", response_model=FavoritesList)
async def get_favorites(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Get all favorites for the current user.
    Returns a list of signup_ids that the user has favorited.
    """
    query = text("""
        SELECT signup_id
        FROM auth.user_favorites
        WHERE user_id = :user_id
        ORDER BY created_at DESC
    """)

    result = await session.execute(query, {"user_id": str(current_user.id)})
    rows = result.fetchall()

    return FavoritesList(favorites=[row.signup_id for row in rows])


@router.post("/{signup_id}", response_model=FavoriteResponse)
async def add_favorite(
    signup_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Add a player to favorites.
    """
    # Check if already favorited
    check_query = text("""
        SELECT id FROM auth.user_favorites
        WHERE user_id = :user_id AND signup_id = :signup_id
    """)
    result = await session.execute(check_query, {
        "user_id": str(current_user.id),
        "signup_id": signup_id
    })

    if result.fetchone():
        # Already favorited
        return FavoriteResponse(signup_id=signup_id, is_favorite=True)

    # Add favorite
    insert_query = text("""
        INSERT INTO auth.user_favorites (user_id, signup_id)
        VALUES (:user_id, :signup_id)
    """)

    await session.execute(insert_query, {
        "user_id": str(current_user.id),
        "signup_id": signup_id
    })
    await session.commit()

    return FavoriteResponse(signup_id=signup_id, is_favorite=True)


@router.delete("/{signup_id}", response_model=FavoriteResponse)
async def remove_favorite(
    signup_id: str,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Remove a player from favorites.
    """
    delete_query = text("""
        DELETE FROM auth.user_favorites
        WHERE user_id = :user_id AND signup_id = :signup_id
    """)

    await session.execute(delete_query, {
        "user_id": str(current_user.id),
        "signup_id": signup_id
    })
    await session.commit()

    return FavoriteResponse(signup_id=signup_id, is_favorite=False)
