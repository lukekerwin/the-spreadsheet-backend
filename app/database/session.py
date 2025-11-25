"""
Database Session Configuration

SQLAlchemy async engine and session management for FastAPI.
Provides database connection pooling and session lifecycle management.
"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# ============================================
# DATABASE ENGINE
# ============================================

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
)

# ============================================
# SESSION FACTORY
# ============================================

# Async session factory for FastAPI
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ============================================
# DEPENDENCY INJECTION
# ============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session for FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
