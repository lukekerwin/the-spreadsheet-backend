"""
Player Endpoints

Provides endpoints for fetching player card data and player name searches.
All endpoints require authentication except where noted.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.players import PlayerCard
from app.models.users import User
from app.schemas.search import SearchResult, SearchResultItem
from app.schemas.card import CardData, CardHeader, CardBanner
from app.schemas.common import Item, Pagination
from app.core.auth import require_auth
from app.util.helpers import validate_param, get_count
from app.util.tier_routing import get_player_card_model

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter()



# ===============================================
# GET /players/cards
# ===============================================

@router.get("/cards", response_model=Pagination[CardData])
async def get_player_cards(
    season_id: int,
    league_id: int,
    game_type_id: int,
    pos_group: str,
    player_id: int | None = None,
    player_ids: str | None = None,
    page_number: int = 1,
    page_size: int = 24,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_auth),
):
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")
    if not validate_param("pos_group", pos_group, allowed_values=["C", "W", "D"]):
        raise HTTPException(status_code=400, detail="Invalid pos_group")

    # Get the appropriate model based on user tier (premium vs free)
    Model = get_player_card_model(user)

    # Build the base filter query
    filters = [
        Model.season_id == season_id,
        Model.league_id == league_id,
        Model.game_type_id == game_type_id,
        Model.pos_group == pos_group
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
                filters.append(Model.player_id.in_(id_list))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid player_ids format (must be comma-separated integers)")
    elif player_id is not None:
        # Backward compatibility: support single player_id parameter
        if not validate_param("player_id", player_id, gt=0):
            raise HTTPException(status_code=400, detail="Invalid player_id")
        filters.append(Model.player_id == player_id)

    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number")

    total = await get_count(session, Model, filters)
    statement = select(Model).where(*filters).offset((page_number-1)*page_size).limit(page_size)

    result = await session.execute(statement)
    players = result.scalars().all()

    cards = []
    for row in players:
        header = CardHeader(
            title=str(row.player_name) if row.player_name else "N/A",
            subtitle=[
                Item(label="Position", value=str(row.pos_group) if row.pos_group else "N/A"),
                Item(label="Record", value=f"{row.wins}-{row.losses}-{row.ot_losses}" if row.wins is not None else "N/A"),
                Item(label="Contract", value=f"{float(int(row.contract)/1000000)}M" if row.contract else "N/A")
            ]
        )

        banner = CardBanner(
            overallPercentile=round(float(row.war_percentile)*100) if row.war_percentile != None else "N/A",
            tier=str(row.tier) if row.tier else None,
            logoPath=f"https://spreadsheet-hockey-logos.s3.us-east-1.amazonaws.com/{row.team_name.replace(' ', '%20')}.png" if row.team_name else None
        )

        header_stats = [
            Item(label="P", value=int(row.points) if row.points is not None else "N/A"),
            Item(label="G", value=int(row.goals) if row.goals is not None else "N/A"),
            Item(label="A", value=int(row.assists) if row.assists is not None else "N/A"),
        ]

        ratings = [
            Item(label="OFFENSE", value=round(float(row.war_offense_pct)*100) if row.war_offense_pct != None else "N/A"),
            Item(label="DEFENSE", value=round(float(row.war_defense_pct)*100) if row.war_defense_pct != None else "N/A"),
            Item(label="TEAMMATES", value=round(float(row.team_percentile)*100) if row.team_percentile != None else "N/A"),
            Item(label="OPPONENTS", value=round(float(row.sos_percentile)*100) if row.sos_percentile != None else "N/A"),
        ]

        stats = [
            Item(label="iOFF", value=f"{round(float(row.ioff * 100), 1)}%" if row.ioff is not None else "N/A"),
            Item(label="xG", value=round(float(row.xg), 1) if row.xg is not None else "N/A"),
            Item(label="xA", value=round(float(row.xa), 1) if row.xa is not None else "N/A"),
            Item(label="GF", value=int(row.gf) if row.gf else "N/A"),
            Item(label="iDEF", value=f"{round(float(row.idef * 100), 1)}%" if row.idef is not None else "N/A"),
            Item(label="TAKE", value=int(row.takeaways) if row.takeaways else "N/A"),
            Item(label="INT", value=int(row.interceptions) if row.interceptions else "N/A"),
            Item(label="GA", value=int(row.ga) if row.ga else "N/A"),
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
    if players:
        last_row = players[-1]
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
# GET /players/cards/names
# ===============================================

@router.get("/cards/names", response_model=SearchResult)
async def get_player_cards_search(
    season_id: int,
    league_id: int,
    game_type_id: int,
    pos_group: str,
    session: AsyncSession = Depends(get_db),
):
    # Validate parameters
    if not validate_param("season_id", season_id, gt=45, lt=53):
        raise HTTPException(status_code=400, detail="Invalid season_id")
    if not validate_param("league_id", league_id, allowed_values=[37,38,84,39,112]):
        raise HTTPException(status_code=400, detail="Invalid league_id")
    if not validate_param("game_type_id", game_type_id, allowed_values=[1, 2]):
        raise HTTPException(status_code=400, detail="Invalid game_type_id")
    if not validate_param("pos_group", pos_group, allowed_values=["C", "W", "D"]):
        raise HTTPException(status_code=400, detail="Invalid pos_group")

    # Build the base filter query
    filters = [
        PlayerCard.season_id == season_id,
        PlayerCard.league_id == league_id,
        PlayerCard.game_type_id == game_type_id,
        PlayerCard.pos_group == pos_group,
    ]

    statement = select(PlayerCard).where(*filters).order_by(PlayerCard.player_name.asc())

    result = await session.execute(statement)
    players = result.scalars().all()

    search_results = []
    for row in players:
        search_results.append(
            SearchResultItem(id=row.player_id, name=row.player_name)
        )

    return SearchResult(
        results=search_results
    )