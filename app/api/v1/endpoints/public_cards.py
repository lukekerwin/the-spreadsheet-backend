"""Public card endpoints - no authentication required.

These endpoints return only the first page of data with default filters:
- Season 53 (current season)
- League 37 (NHL)
- Game Type 1
- Page 1, 24 items per page
- No player/goalie/team filtering
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.players import PlayerCard
from app.models.goalies import GoalieCard
from app.models.teams import TeamCard
from app.schemas.card import CardData, CardHeader, CardBanner
from app.schemas.common import Item, Pagination
from app.util.helpers import get_count

router = APIRouter()

# Public defaults
DEFAULT_SEASON_ID = 53
DEFAULT_LEAGUE_ID = 37
DEFAULT_GAME_TYPE_ID = 1
DEFAULT_PAGE_NUMBER = 1
DEFAULT_PAGE_SIZE = 24


# ===============================================
# GET /public/cards/player
# ===============================================

@router.get("/cards/player", response_model=Pagination[CardData])
async def get_public_player_cards(
    session: AsyncSession = Depends(get_db),
):
    """Get first page of player cards with default filters (no auth required).

    Returns first 24 Center (C) position players from Season 53, NHL.

    Args:
        session: Database session

    Returns:
        First page of player cards (24 items, Centers only)
    """
    # Build filters with public defaults - always Centers (C)
    filters = [
        PlayerCard.season_id == DEFAULT_SEASON_ID,
        PlayerCard.league_id == DEFAULT_LEAGUE_ID,
        PlayerCard.game_type_id == DEFAULT_GAME_TYPE_ID,
        PlayerCard.pos_group == "C"
    ]

    total = await get_count(session, PlayerCard, filters)
    statement = (
        select(PlayerCard)
        .where(*filters)
        .offset((DEFAULT_PAGE_NUMBER - 1) * DEFAULT_PAGE_SIZE)
        .limit(DEFAULT_PAGE_SIZE)
    )

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
            teamColor=row.team_color or "#1e293b"
        )
        cards.append(card)

    total_pages = (total + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE
    return Pagination(
        data=cards,
        page=DEFAULT_PAGE_NUMBER,
        page_size=DEFAULT_PAGE_SIZE,
        total=total,
        total_pages=total_pages,
        last_updated=row.last_updated.strftime("%Y-%m-%d") if row.last_updated else "N/A"
    )


# ===============================================
# GET /public/cards/goalie
# ===============================================

@router.get("/cards/goalie", response_model=Pagination[CardData])
async def get_public_goalie_cards(
    session: AsyncSession = Depends(get_db),
):
    """Get first page of goalie cards with default filters (no auth required).

    Args:
        session: Database session

    Returns:
        First page of goalie cards (24 items)
    """
    # Build filters with public defaults
    filters = [
        GoalieCard.season_id == DEFAULT_SEASON_ID,
        GoalieCard.league_id == DEFAULT_LEAGUE_ID,
        GoalieCard.game_type_id == DEFAULT_GAME_TYPE_ID
    ]

    total = await get_count(session, GoalieCard, filters)
    statement = (
        select(GoalieCard)
        .where(*filters)
        .offset((DEFAULT_PAGE_NUMBER - 1) * DEFAULT_PAGE_SIZE)
        .limit(DEFAULT_PAGE_SIZE)
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
            teamColor=row.team_color or "#1e293b"
        )
        cards.append(card)

    total_pages = (total + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE
    return Pagination(
        data=cards,
        page=DEFAULT_PAGE_NUMBER,
        page_size=DEFAULT_PAGE_SIZE,
        total=total,
        total_pages=total_pages,
        last_updated=row.last_updated.strftime("%Y-%m-%d") if row.last_updated else "N/A"
    )


# ===============================================
# GET /public/cards/team
# ===============================================

@router.get("/cards/team", response_model=Pagination[CardData])
async def get_public_team_cards(
    session: AsyncSession = Depends(get_db),
):
    """Get first page of team cards with default filters (no auth required).

    Args:
        session: Database session

    Returns:
        First page of team cards (24 items)
    """
    # Build filters with public defaults
    filters = [
        TeamCard.season_id == DEFAULT_SEASON_ID,
        TeamCard.league_id == DEFAULT_LEAGUE_ID,
        TeamCard.game_type_id == DEFAULT_GAME_TYPE_ID
    ]

    total = await get_count(session, TeamCard, filters)
    statement = (
        select(TeamCard)
        .where(*filters)
        .offset((DEFAULT_PAGE_NUMBER - 1) * DEFAULT_PAGE_SIZE)
        .limit(DEFAULT_PAGE_SIZE)
    )

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
            teamColor=row.team_color or "#1e293b"
        )
        cards.append(card)

    total_pages = (total + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE
    return Pagination(
        data=cards,
        page=DEFAULT_PAGE_NUMBER,
        page_size=DEFAULT_PAGE_SIZE,
        total=total,
        total_pages=total_pages,
        last_updated=row.last_updated.strftime("%Y-%m-%d") if row.last_updated else "N/A"
    )
