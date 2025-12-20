"""API v1 router configuration."""

import os
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.core.users import fastapi_users
from app.core.security import auth_backend
from app.core.oauth import google_oauth_client
from app.core.config import settings

# Debug: Log the SECRET_KEY being used for OAuth router
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"[OAuth Router] SECRET_KEY at router config: {settings.SECRET_KEY[:8]}...")
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

# Debug endpoint to test state token decoding
@api_v1_router.get("/auth/debug-state")
async def debug_state(state: str):
    """Debug endpoint to test state token decoding."""
    import jwt
    from fastapi_users.jwt import decode_jwt

    logger.info(f"[Debug] Attempting to decode state: {state[:50]}...")
    logger.info(f"[Debug] Using SECRET_KEY: {settings.SECRET_KEY[:8]}...")

    try:
        decoded = decode_jwt(state, settings.SECRET_KEY, ["fastapi-users:oauth-state"])
        logger.info(f"[Debug] Decode SUCCESS: {decoded}")
        return {"status": "success", "decoded": decoded}
    except jwt.ExpiredSignatureError as e:
        logger.error(f"[Debug] Token EXPIRED: {e}")
        return {"status": "expired", "error": str(e)}
    except jwt.InvalidSignatureError as e:
        logger.error(f"[Debug] INVALID SIGNATURE: {e}")
        return {"status": "invalid_signature", "error": str(e)}
    except jwt.DecodeError as e:
        logger.error(f"[Debug] Decode ERROR: {e}")
        return {"status": "decode_error", "error": str(e)}
    except Exception as e:
        logger.error(f"[Debug] Unknown ERROR: {type(e).__name__}: {e}")
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}

# Custom OAuth callback that logs everything
@api_v1_router.get("/auth/google/callback-debug")
async def google_callback_debug(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
):
    """Debug callback to see all parameters."""
    logger.info(f"[Callback Debug] code: {code[:20] if code else None}...")
    logger.info(f"[Callback Debug] state: {state[:50] if state else None}...")
    logger.info(f"[Callback Debug] error param: {error}")
    logger.info(f"[Callback Debug] All query params: {dict(request.query_params)}")

    return {
        "code": code[:20] + "..." if code else None,
        "state": state[:50] + "..." if state else None,
        "error": error,
        "all_params": dict(request.query_params)
    }

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
# NOTE: Associate router temporarily disabled to debug callback conflict
# api_v1_router.include_router(
#     fastapi_users.get_oauth_associate_router(google_oauth_client, UserRead, settings.SECRET_KEY),
#     prefix="/auth/google",
#     tags=["auth"],
# )

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
