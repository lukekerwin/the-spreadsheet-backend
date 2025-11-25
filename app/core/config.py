"""
Application Configuration

Pydantic settings management for environment-based configuration.
Loads settings from environment variables with validation and defaults.
"""

import secrets
from typing import Any, List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings

# ============================================
# SETTINGS CLASS
# ============================================

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALGORITHM: str = "HS256"
    API_V1_STR: str = "/api/v1"
    
    # CRITICAL: In production, this MUST be set in environment variables to persist sessions.
    # If not set, a new random key is generated on every server restart, invalidating all existing tokens.
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # 60 minutes * 24 hours * 30 days = 30 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROJECT_NAME: str = "ts-api"
    PROJECT_DESCRIPTION: str = "A FastAPI api project using sqlalchemy"

    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        """Set default DB URLs if missing."""
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                "sqlite+aiosqlite:///./app.db"
                if self.ENVIRONMENT == "development"
                else "postgresql+asyncpg://postgres:postgres@db:5432/ts-api"
            )
        if not self.SYNC_DATABASE_URL:
            self.SYNC_DATABASE_URL = (
                "sqlite:///./app.db"
                if self.ENVIRONMENT == "development"
                else "postgresql://postgres:postgres@db:5432/ts-api"
            )


    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = "noreply@example.com"
    EMAILS_FROM_NAME: Optional[str] = "ts-api"

    FIRST_SUPERUSER: EmailStr = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin"

    # Stripe configuration for subscription management
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID: Optional[str] = None  # Price ID for premium subscription

    # Frontend URL for Stripe redirects
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = {
        "env_file": ".env.dev",
        "case_sensitive": True,
        "extra": "ignore",
    }

# ============================================
# SETTINGS INSTANCE
# ============================================

settings = Settings()
