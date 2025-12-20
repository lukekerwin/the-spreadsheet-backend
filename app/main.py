"""
Main FastAPI Application

Entry point for the FastAPI application with CORS middleware and API routing.
Configures API documentation visibility based on environment.
"""

import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1.api import api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup info
logger.info(f"Starting application with SECRET_KEY: {settings.SECRET_KEY[:8]}...")
logger.info(f"ENVIRONMENT: {settings.ENVIRONMENT}")

# ============================================
# APPLICATION FACTORY
# ============================================

def create_application() -> FastAPI:
    """Create FastAPI app with middleware and routes."""

    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version="0.1.0",
        openapi_url=None if settings.ENVIRONMENT == "production" else f"{settings.API_V1_STR}/openapi.json",
        docs_url=None if settings.ENVIRONMENT == "production" else f"{settings.API_V1_STR}/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else f"{settings.API_V1_STR}/redoc",
    )

    # CORS configuration - matching your old working setup
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    # Clean up origins (strip whitespace)
    ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,  # Only specific domains allowed
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "Origin", "Authorization"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )

    application.include_router(api_v1_router, prefix=settings.API_V1_STR)
    return application

# ============================================
# APPLICATION INSTANCE
# ============================================

app = create_application()

# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": "0.1.0",
        "docs": f"{settings.API_V1_STR}/docs",
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
