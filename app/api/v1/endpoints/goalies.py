"""
Goalie Endpoints

Provides endpoints for fetching goalie card data and goalie name searches.
All endpoints require authentication except where noted.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.goalies import GoalieCard
from app.models.users import User
from app.schemas.card import CardData, CardHeader, CardBanner
from app.schemas.search import SearchResult, SearchResultItem
from app.schemas.common import Item, Pagination
from app.core.auth import require_auth
from app.util.helpers import validate_param, get_count

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter()



# ===============================================
# GET /goalies/cards
# ===============================================

@router.get("/cards", response_model=Pagination[CardData])
async def get_goalie_cards(
    season_id: int,
    league_id: int,
    game_type_id: int,
    player_id: int | None = None,
    player_ids: str | None = None,
    page_number: int = 1,
    page_size: int = 24,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_auth),
):
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 3]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")

    # Build the base filter query
    filters = [
        GoalieCard.season_id == season_id,
        GoalieCard.league_id == league_id,
        GoalieCard.game_type_id == game_type_id
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
                filters.append(GoalieCard.player_id.in_(id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid player_ids format (must be comma-separated integers)")
    elif player_id is not None:
        # Backward compatibility: support single player_id parameter
        if not validate_param("player_id", player_id, gt=0):
            raise HTTPException(status_code=400, detail="Invalid player_id")
        filters.append(GoalieCard.player_id == player_id)

    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number")

    total = await get_count(session, GoalieCard, filters)
    statement = (
        select(GoalieCard)
        .where(*filters)
        .order_by(GoalieCard.overall_percentile.desc().nulls_last())
        .offset((page_number-1)*page_size)
        .limit(page_size)
    )

    result = await session.execute(statement)
    goalies = result.scalars().all()

    cards = []
    for row in goalies:
        header = CardHeader(
            title=str(row.player_name) if row.player_name else "N/A",
            subtitle=[
                Item(label="Position", value='G'),
                Item(label="Record", value=f"{row.wins}-{row.losses}-{row.ot_losses}" if row.wins is not None else "N/A"),
                Item(label="Contract", value=f"{float(int(row.contract)/1000000)}M" if row.contract else "N/A")
            ]
        )

        banner = CardBanner(
            overallPercentile=round(float(row.overall_percentile)*100) if row.overall_percentile != None else "N/A",
            tier=str(row.tier) if row.tier else None,
            logoPath=f"https://spreadsheet-hockey-logos.s3.us-east-1.amazonaws.com/{row.team_name.replace(' ', '%20')}.png" if row.team_name else None
        )

        header_stats = [
            Item(label="SV%", value=round(float(row.save_pct),3) if row.save_pct else "N/A"),
            Item(label="GAA", value=round(float(row.gaa), 2) if row.gaa is not None else "N/A"),
        ]

        ratings = [
            Item(label="GSAX", value=round(float(row.gsax_percentile*100)) if row.gsax_percentile != None else "N/A"),
            Item(label="SUPPORT", value=round(float(row.def_percentile*100)) if row.def_percentile != None else "N/A"),
            Item(label="TEAMMATES", value=round(float(row.team_percentile*100)) if row.team_percentile != None else "N/A"),
            Item(label="OPPONENTS", value=round(float(row.sos_percentile*100)) if row.sos_percentile != None else "N/A"),
        ]

        stats = [
            Item(label="SH", value=int(row.shots_against) if row.shots_against else "N/A"),
            Item(label="GA", value=int(row.goals_against) if row.goals_against else "N/A"),
            Item(label="xGA", value=round(float(row.xga), 1) if row.xga is not None else "N/A"),
            Item(label="GSAX", value=round(float(row.gsax), 1) if row.gsax else "N/A"),
            Item(label="SH/60", value=round(float(row.shots_per_60), 1) if row.shots_per_60 is not None else "N/A"),
            Item(label="GA/60", value=round(float(row.ga_per_60), 1) if row.ga_per_60 is not None else "N/A"),
            Item(label="xGA/60", value=round(float(row.xga_per_60), 1) if row.xga_per_60 is not None else "N/A"),
            Item(label="GSAX/60", value=round(float(row.gsax_per_60), 1) if row.gsax_per_60 is not None else "N/A"),
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
    if goalies:
        last_row = goalies[-1]
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
# GET /goalies/cards/names
# ===============================================

@router.get("/cards/names", response_model=SearchResult)
async def get_goalie_cards_search(
    season_id: int,
    league_id: int,
    game_type_id: int,
    session: AsyncSession = Depends(get_db),
):
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 3]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")

    # Build the base filter query
    filters = [
        GoalieCard.season_id == season_id,
        GoalieCard.league_id == league_id,
        GoalieCard.game_type_id == game_type_id,
    ]

    statement = select(GoalieCard).where(*filters).order_by(GoalieCard.player_name.asc())

    result = await session.execute(statement)
    goalies = result.scalars().all()

    search_results = []
    for row in goalies:
        search_results.append(
            SearchResultItem(id=row.player_id, name=row.player_name)
        )

    return SearchResult(
        results=search_results
    )