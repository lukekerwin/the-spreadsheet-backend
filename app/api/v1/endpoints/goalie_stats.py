"""Goalie stats endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.goalie_stats import GoalieStatsPage
from app.models.users import User
from app.schemas.goalie_stats import GoalieStatsData, TeamFilterOption
from app.schemas.search import SearchResult, SearchResultItem
from app.schemas.common import Pagination
from app.core.auth import require_auth
from app.util.helpers import validate_param, get_count

router = APIRouter()


@router.get("/stats", response_model=Pagination[GoalieStatsData])
async def get_goalie_stats(
    season_id: int,
    league_id: int,
    game_type_id: int,
    player_id: int | None = None,
    player_ids: str | None = None,
    team_name: str | None = None,
    page_number: int = 1,
    page_size: int = 50,
    sort_by: str | None = None,
    sort_order: str = "desc",
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get paginated goalie statistics with filtering and sorting.

    Protected endpoint requiring authentication.

    Args:
        player_id: Single goalie ID (deprecated, use player_ids instead)
        player_ids: Comma-separated list of goalie IDs for comparison (e.g., "123,456,789")
        sort_by: Column to sort by (e.g., 'shots_against', 'gsax', 'overall_rating')
        sort_order: Sort direction ('asc' or 'desc', defaults to 'desc')
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id (must be 46-52)")

    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")

    if not validate_param("game_type_id", game_type_id, allowed_values=[1]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id (only 1 supported)")

    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number (must be > 0)")

    if not validate_param("page_size", page_size, gt=0, lt=501):
        raise HTTPException(status_code=400, detail="Invalid page_size (must be 1-500)")

    # Validate sorting parameters
    SORTABLE_COLUMNS = [
        "player_name", "team_name", "contract", "win", "loss", "otl",
        "shots_against", "xsh", "shots_prevented", "goals_against", "xga",
        "gsax", "gsaa", "shutouts",
        "overall_rating", "teammate_rating", "opponent_rating"
    ]

    if sort_by is not None and sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by column. Must be one of: {', '.join(SORTABLE_COLUMNS)}"
        )

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order (must be 'asc' or 'desc')")

    # Build filters
    filters = [
        GoalieStatsPage.season_id == season_id,
        GoalieStatsPage.league_id == league_id,
        GoalieStatsPage.game_type_id == game_type_id,
    ]

    # Optional goalie filter (supports both single and multiple goalie IDs)
    # Priority: player_ids > player_id (for backward compatibility)
    if player_ids is not None and player_ids != "":
        # Parse comma-separated goalie IDs
        try:
            id_list = [int(id_str.strip()) for id_str in player_ids.split(",") if id_str.strip()]
            # Validate each ID
            for pid in id_list:
                if not validate_param("player_id", pid, gt=0):
                    raise HTTPException(status_code=400, detail=f"Invalid player_id: {pid}")
            # Apply IN filter for multiple goalies
            if id_list:
                filters.append(GoalieStatsPage.player_id.in_(id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid player_ids format (must be comma-separated integers)")
    elif player_id is not None:
        # Backward compatibility: support single player_id parameter
        if not validate_param("player_id", player_id, gt=0):
            raise HTTPException(status_code=400, detail="Invalid player_id")
        filters.append(GoalieStatsPage.player_id == player_id)

    # Optional team_name filter
    if team_name is not None and team_name != "":
        filters.append(GoalieStatsPage.team_name == team_name)

    # Get total count
    total = await get_count(session, GoalieStatsPage, filters)

    # Build query with filtering
    statement = select(GoalieStatsPage).where(*filters)

    # Add sorting if specified
    if sort_by is not None:
        sort_column = getattr(GoalieStatsPage, sort_by)
        if sort_order == "asc":
            statement = statement.order_by(sort_column.asc().nulls_last())
        else:
            statement = statement.order_by(sort_column.desc().nulls_last())
    else:
        # Default sort by overall rating descending
        statement = statement.order_by(GoalieStatsPage.overall_rating.desc().nulls_last())

    # Add pagination
    statement = statement.offset((page_number - 1) * page_size).limit(page_size)

    result = await session.execute(statement)
    goalies = result.scalars().all()

    # Transform to response schema
    stats_data = []
    for goalie in goalies:
        # Create dict from ORM object
        goalie_dict = {
            "season_id": goalie.season_id,
            "league_id": goalie.league_id,
            "game_type_id": goalie.game_type_id,
            "player_id": goalie.player_id,
            "pos_group": goalie.pos_group,
            "player_name": goalie.player_name or "Unknown",
            "team_name": goalie.team_name or "Unknown",
            "win": goalie.win or 0,
            "loss": goalie.loss or 0,
            "otl": goalie.otl or 0,
            "contract": goalie.contract or 0.0,
            "shots_against": goalie.shots_against or 0,
            "xsh": goalie.xsh or 0.0,
            "shots_prevented": goalie.shots_prevented or 0.0,
            "goals_against": goalie.goals_against or 0,
            "xga": goalie.xga or 0.0,
            "gsax": goalie.gsax or 0.0,
            "gsaa": goalie.gsaa or 0.0,
            "shutouts": goalie.shutouts or 0,
            "overall_rating": goalie.overall_rating,
            "teammate_rating": goalie.teammate_rating,
            "opponent_rating": goalie.opponent_rating,
        }

        # Pydantic will handle alias transformation
        stats_data.append(GoalieStatsData(**goalie_dict))

    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size

    # Get last_updated from first record (all should have same value)
    last_updated_str = "N/A"
    if stats_data and len(stats_data) > 0:
        # Query for last_updated from the first matching record
        first_goalie = goalies[0] if goalies else None
        if first_goalie and first_goalie.last_updated:
            last_updated_str = first_goalie.last_updated.strftime("%Y-%m-%d")

    return Pagination(
        data=stats_data,
        page=page_number,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        last_updated=last_updated_str,
    )


@router.get("/stats/filters", response_model=list[TeamFilterOption])
async def get_goalie_stats_filters(
    season_id: int,
    league_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get available teams for goalie stats filtering.

    Returns distinct team names for the given season and league,
    sorted alphabetically.

    Protected endpoint requiring authentication.
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id (must be 46-52)")

    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")

    # Query for distinct team names
    statement = (
        select(distinct(GoalieStatsPage.team_name))
        .where(
            GoalieStatsPage.season_id == season_id,
            GoalieStatsPage.league_id == league_id,
            GoalieStatsPage.team_name.isnot(None)
        )
        .order_by(GoalieStatsPage.team_name)
    )

    result = await session.execute(statement)
    team_names = result.scalars().all()

    # Transform to response schema
    return [TeamFilterOption(team_name=name) for name in team_names]


@router.get("/stats/names", response_model=SearchResult)
async def get_goalie_stats_names(
    season_id: int,
    league_id: int,
    game_type_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """
    Get goalie names for autocomplete in goalie stats page.

    Returns all goalie names matching the given filters,
    sorted alphabetically by player name.

    Protected endpoint requiring authentication.
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id (must be 46-52)")

    if not validate_param("league_id", league_id, allowed_values=[37, 38, 84, 39, 112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")

    if not validate_param("game_type_id", game_type_id, allowed_values=[1]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id (only 1 supported)")

    # Build filters
    filters = [
        GoalieStatsPage.season_id == season_id,
        GoalieStatsPage.league_id == league_id,
        GoalieStatsPage.game_type_id == game_type_id,
    ]

    # Query for goalie names, sorted alphabetically
    statement = (
        select(GoalieStatsPage)
        .where(*filters)
        .order_by(GoalieStatsPage.player_name.asc())
    )

    result = await session.execute(statement)
    goalies = result.scalars().all()

    # Transform to search results
    search_results = []
    for goalie in goalies:
        search_results.append(
            SearchResultItem(id=goalie.player_id, name=goalie.player_name or "Unknown")
        )

    return SearchResult(results=search_results)
