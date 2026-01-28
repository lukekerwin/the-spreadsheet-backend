"""
Team Endpoints

Provides endpoints for fetching team card data, team name searches, and strength of schedule data.
All endpoints require authentication except where noted.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, distinct, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.teams import TeamCard, TeamSOS
from app.models.users import User
from app.schemas.card import CardData, CardHeader, CardBanner
from app.schemas.search import SearchResult, SearchResultItem
from app.schemas.common import Item, Pagination
from app.schemas.team_sos import TeamSOSData
from app.core.auth import require_auth
from app.util.helpers import validate_param, get_count
from app.util.tier_routing import get_team_card_model

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter()



# ===============================================
# GET /teams/cards
# ===============================================

@router.get("/cards", response_model=Pagination[CardData])
async def get_team_cards(
    season_id: int,
    league_id: int,
    game_type_id: int,
    team_id: int | None = None,
    page_number: int = 1,
    page_size: int = 24,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=54):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")

    # Get the appropriate model based on user tier (premium vs free)
    Model = get_team_card_model(user)

    # Build the base filter query
    filters = [
        Model.season_id == season_id,
        Model.league_id == league_id,
        Model.game_type_id == game_type_id
    ]

    if team_id is not None:
        if not validate_param("team_id", team_id, gt=0):
            raise HTTPException(status_code=400, detail="Invalid team_id")
        filters.append(Model.team_id == team_id)

    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number")

    total = await get_count(session, Model, filters)
    statement = select(Model).where(*filters).offset((page_number-1)*page_size).limit(page_size)

    result = await session.execute(statement)
    teams = result.scalars().all()

    cards = []
    for row in teams:
        header = CardHeader(
            title=str(row.team_name) if row.team_name else "N/A",
            subtitle=[
                Item(label="Record", value=f"{row.wins}-{row.losses}-{row.ot_losses}" if row.wins is not None else "N/A"),
                Item(label="Points", value=f"{(row.wins*2)+row.ot_losses} pts" if row.wins is not None else "N/A")
            ]
        )

        banner = CardBanner(
            overallPercentile=round(float(row.overall_percentile)*100) if row.overall_percentile != None else "N/A",
            tier=str(row.overall_tier) if row.overall_tier else None,
            logoPath=f"https://spreadsheet-hockey-logos.s3.us-east-1.amazonaws.com/{row.team_full_name.replace(' ', '%20')}.png" if row.team_name else None
        )

        header_stats = [
            Item(label="GF", value=int(row.total_goals) if row.total_goals else "N/A"),
            Item(label="GA", value=int(row.total_goals_against) if row.total_goals_against else "N/A"),
        ]

        ratings = [
            Item(label="OFFENSE", value=round(float(row.offense_percentile)*100) if row.offense_percentile != None else "N/A"),
            Item(label="DEFENSE", value=round(float(row.defense_percentile)*100) if row.defense_percentile != None else "N/A"),
            Item(label="GOALIES", value=round(float(row.goalie_percentile)*100) if row.goalie_percentile != None else "N/A"),
            Item(label="OPPONENTS", value=round(float(row.opponents_percentile)*100) if row.opponents_percentile != None else "N/A"),
        ]

        stats = [
            Item(label="xG", value=round(float(row.total_xg), 1) if row.total_xg else "N/A"),
            Item(label="GF/60", value=round(float(row.goals_per_60), 1) if row.goals_per_60 else "N/A"),
            Item(label="xGA", value=round(float(row.total_opponent_xg), 1) if row.total_opponent_xg else "N/A"),
            Item(label="GA/60", value=round(float(row.ga_per_60), 1) if row.ga_per_60 else "N/A"),
        ]

        card = CardData(
            header=header,
            banner=banner,
            headerStats=header_stats,
            ratings=ratings,
            stats=stats,
            teamColor=row.team_color or "#1e293b",
        )
        cards.append(card)
    
    total_pages = (total + page_size - 1) // page_size

    # Get last_updated from the last row, or "N/A" if no results
    last_updated_str = "N/A"
    if teams:
        last_row = teams[-1]
        if last_row.last_updated:
            last_updated_str = last_row.last_updated.strftime("%Y-%m-%d")

    return Pagination(
        data=cards,
        page=page_number,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        last_updated=last_updated_str
    )

# ===============================================
# GET /teams/cards/names
# ===============================================

@router.get("/cards/names", response_model=SearchResult)
async def get_team_cards_search(
    season_id: int,
    league_id: int,
    game_type_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=54):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")

    # Get the appropriate model based on user tier (premium vs free)
    Model = get_team_card_model(user)

    # Build the base filter query
    filters = [
        Model.season_id == season_id,
        Model.league_id == league_id,
        Model.game_type_id == game_type_id,
    ]

    statement = select(Model).where(*filters).order_by(Model.team_full_name.asc())

    result = await session.execute(statement)
    teams = result.scalars().all()

    search_results = []
    for row in teams:
        search_results.append(
            SearchResultItem(id=row.team_id, name=row.team_full_name)
        )

    return SearchResult(
        results=search_results
    )


# ===============================================
# GET /teams/sos/filters
# ===============================================

@router.get("/sos/filters")
async def get_team_sos_filters(
    season_id: int,
    league_id: int,
    game_type_id: int = 1,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """Get distinct combinations of week_id and game_dow for team SOS filters.

    Returns unique weeks and days of week available for the given season, league, and game type.
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=54):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")

    # Query for distinct week_ids and game_dow values

    weeks_statement = (
        select(distinct(TeamSOS.week_id))
        .where(
            and_(
                TeamSOS.season_id == season_id,
                TeamSOS.league_id == league_id,
                TeamSOS.game_type_id == game_type_id,
            )
        )
        .order_by(TeamSOS.week_id)
    )

    days_statement = (
        select(distinct(TeamSOS.game_dow))
        .where(
            and_(
                TeamSOS.season_id == season_id,
                TeamSOS.league_id == league_id,
                TeamSOS.game_type_id == game_type_id,
            )
        )
        .order_by(TeamSOS.game_dow)
    )

    weeks_result = await session.execute(weeks_statement)
    days_result = await session.execute(days_statement)

    weeks = [row[0] for row in weeks_result.all()]
    days = [row[0] for row in days_result.all()]

    # Map week_id values to labels (0 = All Weeks/Season)
    week_options = []
    for week in weeks:
        if week == 0:
            week_options.append({"label": "All Weeks", "value": week})
        else:
            week_options.append({"label": f"Week {week}", "value": week})

    # Map day of week numbers to names (0 = Sunday, -1 = All Days)
    day_names = {
        -1: "All Days",
        0: "Sunday",
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday"
    }

    day_options = [{"label": day_names.get(day, f"Day {day}"), "value": day} for day in days]

    return {
        "weeks": week_options,
        "days_of_week": day_options
    }


# ===============================================
# GET /teams/sos/data
# ===============================================

@router.get("/sos/data", response_model=list[TeamSOSData])
async def get_team_sos_data(
    season_id: int,
    league_id: int,
    game_type_id: int = 1,
    week_id: int = 0,
    game_dow: int = -1,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    """Get team strength of schedule data.

    Parameters:
    - game_type_id: 1 for regular season, 2 for playoffs
    - week_id: 0 for all weeks/season aggregate, > 0 for specific week
    - game_dow: -1 for all days/weekly aggregate, 0-6 for specific day (0=Sunday)
    """
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=54):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")

    # Build filters
    filters = [
        TeamSOS.season_id == season_id,
        TeamSOS.league_id == league_id,
        TeamSOS.game_type_id == game_type_id,
        TeamSOS.week_id == week_id,
        TeamSOS.game_dow == game_dow,
    ]

    # Build query with ordering
    statement = (
        select(TeamSOS)
        .where(*filters)
        .order_by(TeamSOS.opponent_rating.desc())  # Order by opponent rating (SOS)
    )

    result = await session.execute(statement)
    teams = result.scalars().all()

    # Convert to response schema
    data = [
        TeamSOSData(
            season_id=team.season_id,
            league_id=team.league_id,
            game_type_id=team.game_type_id,
            week_id=team.week_id,
            game_dow=team.game_dow,
            team_id=team.team_id,
            team_name=team.team_name,
            win=team.win,
            loss=team.loss,
            otl=team.otl,
            teammate_win_pct=float(team.teammate_win_pct) if team.teammate_win_pct else None,
            opponent_win_pct=float(team.opponent_win_pct) if team.opponent_win_pct else None,
            teammate_rating=float(team.teammate_rating) if team.teammate_rating else None,
            opponent_rating=float(team.opponent_rating) if team.opponent_rating else None,
        )
        for team in teams
    ]

    return data