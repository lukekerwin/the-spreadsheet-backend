"""
Playoff Odds API endpoints

Provides playoff probabilities and seeding projections based on Monte Carlo simulations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.playoff_odds import PlayoffOdds
from app.schemas.playoff_odds import PlayoffOddsResponse
from app.core.auth import require_auth
from app.models.users import User

router = APIRouter()


@router.get("/data", response_model=list[PlayoffOddsResponse])
async def get_playoff_odds(
    season_id: int = Query(..., description="Season ID (e.g., 52)"),
    league_id: int = Query(..., description="League ID (e.g., 37 for NHL)"),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get playoff odds for all teams in a league.

    Returns playoff probabilities and seeding projections based on Monte Carlo
    simulations of the remaining season. Includes:
    - Overall playoff probability
    - Probabilities for each playoff seed (1-8)
    - Current standings
    - Games remaining

    **Authentication required.**

    Args:
        season_id: Season ID to query
        league_id: League ID to query (37=NHL, 38=AHL, etc.)

    Returns:
        List of playoff odds for each team, sorted by playoff probability descending
    """
    # Query playoff odds
    statement = (
        select(PlayoffOdds)
        .where(PlayoffOdds.season_id == season_id)
        .where(PlayoffOdds.league_id == league_id)
        .order_by(PlayoffOdds.playoff_odds.desc())
    )

    result = await session.execute(statement)
    odds = result.scalars().all()

    if not odds:
        raise HTTPException(
            status_code=404,
            detail=f"No playoff odds found for season {season_id}, league {league_id}. "
                   "Run the simulation script to generate data."
        )

    return [PlayoffOddsResponse.model_validate(o) for o in odds]


@router.get("/{team_id}", response_model=PlayoffOddsResponse)
async def get_team_playoff_odds(
    team_id: int,
    season_id: int = Query(..., description="Season ID (e.g., 52)"),
    league_id: int = Query(..., description="League ID (e.g., 37 for NHL)"),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get playoff odds for a specific team.

    **Authentication required.**

    Args:
        team_id: Team ID
        season_id: Season ID to query
        league_id: League ID to query

    Returns:
        Playoff odds for the specified team
    """
    statement = (
        select(PlayoffOdds)
        .where(PlayoffOdds.season_id == season_id)
        .where(PlayoffOdds.league_id == league_id)
        .where(PlayoffOdds.team_id == team_id)
    )

    result = await session.execute(statement)
    odds = result.scalar_one_or_none()

    if not odds:
        raise HTTPException(
            status_code=404,
            detail=f"Playoff odds not found for team {team_id} in season {season_id}, league {league_id}"
        )

    return PlayoffOddsResponse.model_validate(odds)
