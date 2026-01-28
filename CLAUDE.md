# CLAUDE.md - API

This file provides guidance to Claude Code (claude.ai/code) when working with the API component.

## Overview

FastAPI-based REST API serving player and goalie data with Google OAuth authentication. Uses async SQLAlchemy for database operations and fastapi-users for authentication management.

## Quick Start

```bash
# Start development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Run specific test
pytest tests/unit/test_file.py -v

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Access API docs (development only)
# http://localhost:8000/api/v1/docs (Swagger)
# http://localhost:8000/api/v1/redoc (ReDoc)
```

## Project Structure

```
app/
├── api/v1/
│   ├── api.py              # Main router aggregation
│   └── endpoints/          # API endpoint modules
│       ├── players.py      # Player endpoints
│       ├── goalies.py      # Goalie endpoints
│       ├── teams.py        # Team endpoints
│       ├── public_cards.py # Public player cards
│       └── api_keys.py     # API key management
├── core/
│   ├── config.py          # Settings and configuration
│   └── auth.py            # Authentication dependencies
├── database/
│   └── session.py         # Database session management
├── models/                # SQLAlchemy ORM models
│   ├── players.py
│   ├── goalies.py
│   ├── teams.py
│   └── users.py
├── schemas/               # Pydantic request/response schemas
│   ├── card.py
│   ├── search.py
│   └── common.py
├── users/                 # User management
│   ├── manager.py         # fastapi-users manager
│   └── dependencies.py    # User dependencies
├── util/                  # Helper utilities
│   └── helpers.py         # Validation and helper functions
└── main.py                # FastAPI app creation and config

migrations/                # Alembic migration files
tests/                     # Test suite
```

## Architecture Pattern

The API uses a **direct endpoint-to-database** pattern:

```python
@router.get("/cards", response_model=Pagination[CardData])
async def get_player_cards(
    season_id: int,
    league_id: int,
    game_type_id: int,
    pos_group: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),  # Auth required
):
    # 1. Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=54):
        raise HTTPException(status_code=400, detail="Invalid season_id")

    # 2. Build query
    filters = [PlayerCard.season_id == season_id, ...]
    statement = select(PlayerCard).where(*filters).offset(offset).limit(limit)

    # 3. Execute query
    result = await session.execute(statement)
    players = result.scalars().all()

    # 4. Transform and return
    return Pagination(items=[...], total=total)
```

## Key Patterns

### Authentication

All endpoints (except public ones) require authentication via `require_auth` dependency:

```python
from app.core.auth import require_auth
from app.models.users import User

@router.get("/protected")
async def protected_route(
    current_user: User = Depends(require_auth)
):
    return {"user_id": current_user.id}
```

### Database Sessions

Use `get_db` dependency for async database sessions:

```python
from app.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/data")
async def get_data(
    session: AsyncSession = Depends(get_db)
):
    result = await session.execute(select(Model).where(...))
    return result.scalars().all()
```

### Parameter Validation

Use `validate_param` utility for consistent validation:

```python
from app.util.helpers import validate_param

# Greater than validation
if not validate_param("page_number", page_number, gt=0):
    raise HTTPException(status_code=400, detail="Invalid page_number")

# Allowed values validation
if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
    raise HTTPException(status_code=400, detail="Invalid league_id")
```

### Pagination

Use `Pagination` schema for paginated responses:

```python
from app.schemas.common import Pagination

@router.get("/items", response_model=Pagination[ItemSchema])
async def get_items(
    page_number: int = 1,
    page_size: int = 24,
    session: AsyncSession = Depends(get_db)
):
    offset = (page_number - 1) * page_size
    total = await get_count(session, filters)

    statement = select(Model).where(*filters).offset(offset).limit(page_size)
    result = await session.execute(statement)

    return Pagination(
        items=[...],
        total=total,
        page_number=page_number,
        page_size=page_size
    )
```

## Configuration

Settings are managed via Pydantic BaseSettings in `app/core/config.py`:

```python
from app.core.config import settings

# Access configuration
database_url = settings.DATABASE_URL
api_prefix = settings.API_V1_STR
environment = settings.ENVIRONMENT
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth secret
- `FRONTEND_URL` - Frontend URL for CORS and OAuth redirects
- `ENVIRONMENT` - "development" or "production" (affects docs visibility)

## Database Models

SQLAlchemy ORM models follow async pattern:

```python
from sqlalchemy import Column, Integer, String
from app.database.base import Base

class PlayerCard(Base):
    __tablename__ = "player_cards"
    __table_args__ = {"schema": "analytics"}

    player_id = Column(Integer, primary_key=True)
    player_name = Column(String)
    season_id = Column(Integer)
    # ... more columns
```

## Response Schemas

Pydantic schemas for type-safe responses:

```python
from pydantic import BaseModel

class CardData(BaseModel):
    header: CardHeader
    banner: CardBanner
    stats: list[StatItem]

    class Config:
        from_attributes = True  # Enables ORM mode
```

## Migrations

Alembic handles database schema migrations:

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add new column to players"

# Review generated migration in migrations/versions/

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## CORS Configuration

CORS is configured in `app/main.py`:

```python
# Allowed origins from environment variable (comma-separated)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

application.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Origin", "Authorization"],
    max_age=3600,
)
```

## Authentication Flow

1. **Google OAuth Authorization**: User redirects to `/api/v1/auth/google/authorize`
2. **Callback**: Google redirects to frontend `/auth/callback` with code
3. **Token Exchange**: Frontend sends code to `/api/v1/auth/google/callback`
4. **Session Creation**: API creates session and returns httpOnly cookie
5. **Authenticated Requests**: Cookie automatically included in subsequent requests

## Common Tasks

### Adding a New Endpoint

1. Create endpoint function in appropriate module under `app/api/v1/endpoints/`
2. Add Pydantic schema if needed in `app/schemas/`
3. Use `require_auth` dependency if protected
4. Add validation using `validate_param` utility
5. Return appropriate Pydantic response model
6. Endpoint will be auto-discovered via router in `app/api/v1/api.py`

### Adding a New Model

1. Create model in `app/models/`
2. Import in `app/database/base.py` for migration detection
3. Run `alembic revision --autogenerate -m "Add model"`
4. Review and apply migration

### Debugging Database Queries

Enable SQL logging by setting environment variable:
```bash
ECHO_SQL=1 uvicorn app.main:app --reload
```

## Production Deployment

- API docs automatically disabled when `ENVIRONMENT=production`
- Uses Railway with nixpacks configuration
- Requires all environment variables set in Railway
- Database migrations must be run manually after deployment

## Common Issues

**"relation does not exist"**: Run `alembic upgrade head` to apply migrations

**CORS errors**: Check `ALLOWED_ORIGINS` includes frontend URL

**Auth not working**: Verify `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `FRONTEND_URL` are set correctly

**Connection pool errors**: Check database connection string and PostgreSQL accessibility
