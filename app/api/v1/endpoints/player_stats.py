"""
Player Stats Endpoints

Provides endpoints for fetching detailed player statistics with filtering, sorting, and pagination.
Includes team filter options and player name searches for the stats view.
All endpoints require authentication.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.player_stats import PlayerStatsPage
from app.models.users import User
from app.schemas.player_stats import PlayerStatsData, TeamFilterOption
from app.schemas.search import SearchResult, SearchResultItem
from app.schemas.common import Pagination
from app.core.auth import require_auth
from app.util.helpers import validate_param, get_count

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter()

# ============================================
# CONSTANTS
# ============================================

SORTABLE_COLUMNS = [
    "player_name", "team_name", "contract", "win", "loss", "otl",
    "points", "goals", "assists", "plus_minus",
    "xg", "xa", "gax", "aax", "ioff", "off_gar",
    "interceptions", "takeaways", "blocks", "idef", "def_gar",
    "overall_rating", "offense_rating", "defense_rating",
    "teammate_rating", "opponent_rating"
]

# ============================================
# ENDPOINTS
# ============================================


@router.get("/stats", response_model=Pagination[PlayerStatsData])
async def get_player_stats(
    season_id: int,
    league_id: int,
    game_type_id: int,
    pos_group: str,
    player_id: int | None = None,
    player_ids: str | None = None,
    team_name: str | None = None,
    page_number: int = 1,
    page_size: int = 100,
    sort_by: str | None = None,
    sort_order: str = "desc",
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get paginated player statistics with filtering and sorting.

    Protected endpoint requiring authentication.

    Args:
        player_id: Single player ID (deprecated, use player_ids instead)
        player_ids: Comma-separated list of player IDs for comparison (e.g., "123,456,789")
        sort_by: Column to sort by (e.g., 'points', 'goals', 'overall_rating')
        sort_order: Sort direction ('asc' or 'desc', defaults to 'desc')
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id (must be 46-52)")

    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")

    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 3]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id (must be 1 or 3)")

    if not validate_param("pos_group", pos_group, allowed_values=["C", "W", "D"]):
        raise HTTPException(status_code=400, detail="Invalid pos_group (must be C, W, or D)")

    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number (must be > 0)")

    if not validate_param("page_size", page_size, gt=0, lt=501):
        raise HTTPException(status_code=400, detail="Invalid page_size (must be 1-500)")

    # Validate sorting parameters
    if sort_by is not None and sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by column. Must be one of: {', '.join(SORTABLE_COLUMNS)}"
        )

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order (must be 'asc' or 'desc')")

    # Build filters
    filters = [
        PlayerStatsPage.season_id == season_id,
        PlayerStatsPage.league_id == league_id,
        PlayerStatsPage.game_type_id == game_type_id,
        PlayerStatsPage.pos_group == pos_group,
    ]

    # Optional player filter (supports both single and multiple player IDs)
    # Priority: player_ids > player_id (for backward compatibility)
    if player_ids is not None and player_ids != "":
        # Parse comma-separated player IDs
        try:
            id_list = [int(id_str.strip()) for id_str in player_ids.split(",") if id_str.strip()]
            # Validate each ID
            for pid in id_list:
                if not validate_param("player_id", pid, gt=0):
                    raise HTTPException(status_code=400, detail=f"Invalid player_id: {pid}")
            # Apply IN filter for multiple players
            if id_list:
                filters.append(PlayerStatsPage.player_id.in_(id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid player_ids format (must be comma-separated integers)")
    elif player_id is not None:
        # Backward compatibility: support single player_id parameter
        if not validate_param("player_id", player_id, gt=0):
            raise HTTPException(status_code=400, detail="Invalid player_id")
        filters.append(PlayerStatsPage.player_id == player_id)

    # Optional team_name filter
    if team_name is not None and team_name != "":
        filters.append(PlayerStatsPage.team_name == team_name)

    # Get total count
    total = await get_count(session, PlayerStatsPage, filters)

    # Build query with filtering
    statement = select(PlayerStatsPage).where(*filters)

    # Add sorting if specified
    if sort_by is not None:
        sort_column = getattr(PlayerStatsPage, sort_by)
        if sort_order == "asc":
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())
    else:
        # Default sort by overall rating descending
        statement = statement.order_by(PlayerStatsPage.overall_rating.desc().nulls_last())

    # Add pagination
    statement = statement.offset((page_number - 1) * page_size).limit(page_size)

    result = await session.execute(statement)
    players = result.scalars().all()

    # Transform to response schema
    stats_data = []
    for player in players:
        # Create dict from ORM object
        player_dict = {
            "season_id": player.season_id,
            "league_id": player.league_id,
            "game_type_id": player.game_type_id,
            "player_id": player.player_id,
            "pos_group": player.pos_group,
            "player_name": player.player_name or "Unknown",
            "team_name": player.team_name or "Unknown",
            "win": player.win or 0,
            "loss": player.loss or 0,
            "otl": player.otl or 0,
            "contract": player.contract or 0.0,
            "points": player.points or 0,
            "goals": player.goals or 0,
            "assists": player.assists or 0,
            "plus_minus": player.plus_minus or 0,
            "xg": player.xg or 0.0,
            "xa": player.xa or 0.0,
            "gax": player.gax or 0.0,
            "aax": player.aax or 0.0,
            "ioff": (player.ioff or 0.0) * 100,  # Convert ratio to percentage
            "off_gar": player.off_gar or 0.0,
            "interceptions": player.interceptions or 0,
            "takeaways": player.takeaways or 0,
            "blocks": player.blocks or 0,
            "idef": (player.idef or 0.0) * 100,  # Convert ratio to percentage
            "def_gar": player.def_gar or 0.0,
            "overall_rating": player.overall_rating,
            "offense_rating": player.offense_rating,
            "defense_rating": player.defense_rating,
            "teammate_rating": player.teammate_rating,
            "opponent_rating": player.opponent_rating,
        }

        # Pydantic will handle alias transformation
        stats_data.append(PlayerStatsData(**player_dict))

    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size

    # Get last_updated from first record (all should have same value)
    last_updated_str = "N/A"
    if stats_data and len(stats_data) > 0:
        # Query for last_updated from the first matching record
        first_player = players[0] if players else None
        if first_player and first_player.last_updated:
            last_updated_str = first_player.last_updated.strftime("%Y-%m-%d")

    return Pagination(
        data=stats_data,
        page=page_number,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        last_updated=last_updated_str,
    )


@router.get("/stats/filters", response_model=list[TeamFilterOption])
async def get_player_stats_filters(
    season_id: int,
    league_id: int,
    game_type_id: int = 1,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get available teams for player stats filtering.

    Returns distinct team names for the given season, league, and game type,
    sorted alphabetically.

    Protected endpoint requiring authentication.
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id (must be 46-52)")

    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")

    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 3]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id (must be 1 or 3)")

    # Query for distinct team names
    statement = (
        select(distinct(PlayerStatsPage.team_name))
        .where(
            PlayerStatsPage.season_id == season_id,
            PlayerStatsPage.league_id == league_id,
            PlayerStatsPage.game_type_id == game_type_id,
            PlayerStatsPage.team_name.isnot(None)
        )
        .order_by(PlayerStatsPage.team_name)
    )

    result = await session.execute(statement)
    team_names = result.scalars().all()

    # Transform to response schema
    return [TeamFilterOption(team_name=name) for name in team_names]


@router.get("/stats/names", response_model=SearchResult)
async def get_player_stats_names(
    season_id: int,
    league_id: int,
    game_type_id: int,
    pos_group: str,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get player names for autocomplete in player stats page.

    Returns all player names matching the given filters,
    sorted alphabetically by player name.

    Protected endpoint requiring authentication.
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id (must be 46-52)")

    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")

    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 3]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id (must be 1 or 3)")

    if not validate_param("pos_group", pos_group, allowed_values=["C", "W", "D"]):
        raise HTTPException(status_code=400, detail="Invalid pos_group (must be C, W, or D)")

    # Build filters
    filters = [
        PlayerStatsPage.season_id == season_id,
        PlayerStatsPage.league_id == league_id,
        PlayerStatsPage.game_type_id == game_type_id,
        PlayerStatsPage.pos_group == pos_group,
    ]

    # Query for player names, sorted alphabetically
    statement = (
        select(PlayerStatsPage)
        .where(*filters)
        .order_by(PlayerStatsPage.player_name.asc())
    )

    result = await session.execute(statement)
    players = result.scalars().all()

    # Transform to search results
    search_results = []
    for player in players:
        search_results.append(
            SearchResultItem(id=player.player_id, name=player.player_name or "Unknown")
        )

    return SearchResult(results=search_results)
