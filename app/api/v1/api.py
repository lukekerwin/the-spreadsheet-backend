"""API v1 router configuration."""

import os
from fastapi import APIRouter
from app.core.users import fastapi_users
from app.core.security import auth_backend
from app.core.oauth import google_oauth_client
from app.core.config import settings
from app.api.v1.endpoints import (
    players,
    goalies,
    teams,
    api_keys,
    public_cards,
    player_stats,
    goalie_stats,
    playoff_odds,
    subscriptions,
    bidding_package,
    favorites,
)
from app.schemas.user import UserRead, UserCreate, UserUpdate

api_v1_router = APIRouter()

# FastAPI-Users routers
api_v1_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)
api_v1_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
api_v1_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
api_v1_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Google OAuth router
# Determine redirect URL based on environment
# In production, use the FRONTEND_URL env var, in development use localhost
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
OAUTH_REDIRECT_URL = f"{FRONTEND_URL}/auth/callback/google"

api_v1_router.include_router(
    fastapi_users.get_oauth_router(
        google_oauth_client,
        auth_backend,
        settings.SECRET_KEY,  # Secret for state token - MUST be set in production env
        redirect_url=OAUTH_REDIRECT_URL,  # Frontend callback
        associate_by_email=True,  # Auto-link accounts with same email
        is_verified_by_default=True,  # Trust Google-verified emails
    ),
    prefix="/auth/google",
    tags=["auth"],
)
api_v1_router.include_router(
    fastapi_users.get_oauth_associate_router(google_oauth_client, UserRead, settings.SECRET_KEY),
    prefix="/auth/google",
    tags=["auth"],
)

# Custom routers
api_v1_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_v1_router.include_router(public_cards.router, prefix="/public", tags=["Public"])
api_v1_router.include_router(players.router, prefix="/players", tags=["Players"])
api_v1_router.include_router(player_stats.router, prefix="/players", tags=["Players"])
api_v1_router.include_router(goalies.router, prefix="/goalies", tags=["Goalies"])
api_v1_router.include_router(goalie_stats.router, prefix="/goalies", tags=["Goalies"])
api_v1_router.include_router(teams.router, prefix="/teams", tags=['Teams'])
api_v1_router.include_router(playoff_odds.router, prefix="/playoff-odds", tags=["Playoff Odds"])
api_v1_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_v1_router.include_router(bidding_package.router, prefix="/bidding-package", tags=["Bidding Package"])
api_v1_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
