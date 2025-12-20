"""
Bidding Package Endpoints

Endpoints for fetching bidding package data (requires one-time purchase).
Combines player signups with their historical stats and ratings.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.users import User
from app.schemas.bidding_package import BiddingPackageData
from app.schemas.bidding_package_player import (
    BiddingPackagePlayerDetail,
    PlayerBasicInfo,
    PlayerSeasonStats,
)
from app.schemas.common import Pagination
from app.core.auth import require_bidding_package
from app.util.helpers import validate_param

# ============================================
# ROUTER CONFIGURATION
# ============================================

router = APIRouter()

# ============================================
# CONSTANTS
# ============================================

SORTABLE_COLUMNS = [
    "player_name",
    "position",
    "pos_group",
    "status",
    "server",
    "console",
    "is_rostered",
    "last_season_id",
    "last_league_name",
    "games_played",
    "wins",
    "losses",
    "points",
    "war_percentile",
    "team_percentile",
    "sos_percentile",
]

ALLOWED_POS_GROUPS = ["F", "D", "G", "C", "W"]
ALLOWED_POSITIONS = ["LW", "C", "RW", "LD", "RD", "G"]
ALLOWED_SERVERS = ["East", "Central", "West"]
ALLOWED_CONSOLES = ["PS5", "Xbox Series X|S"]
ALLOWED_LEAGUE_IDS = [37, 38, 39, 84, 112]  # LGHL, LGAHL, LGCHL, LGECHL, LGNCAA

# ============================================
# ENDPOINTS
# ============================================


@router.get("/data", response_model=Pagination[BiddingPackageData])
async def get_bidding_package_data(
    search: str | None = None,
    position: str | None = None,
    pos_group: str | None = None,
    server: str | None = None,
    console: str | None = None,
    show_rostered: bool = True,
    last_season_id: int | None = None,
    last_league_id: int | None = None,
    page_number: int = 1,
    page_size: int = 50,
    sort_by: str = "war_percentile",
    sort_order: str = "desc",
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_bidding_package),
):
    """
    Get paginated bidding package data with filtering and sorting.

    Requires one-time Bidding Package purchase.

    Args:
        search: Search player names (case-insensitive partial match)
        pos_group: Filter by position group (F, D, G, C, W)
        server: Filter by server (East, Central, West)
        console: Filter by console (PS5, Xbox Series X|S)
        show_rostered: Include players already on rosters (default True)
        last_season_id: Filter by last season played
        last_league_id: Filter by last league played (37=LGHL, 38=LGAHL, etc.)
        page_number: Page number (default 1)
        page_size: Items per page (default 50, max 200)
        sort_by: Column to sort by (default: war_percentile)
        sort_order: Sort direction (asc/desc, default: desc)

    Returns:
        Paginated bidding package data with signup info, last season stats, and ratings.
    """
    # Validate pagination
    if not validate_param("page_number", page_number, gt=0):
        raise HTTPException(status_code=400, detail="Invalid page_number (must be > 0)")

    if not validate_param("page_size", page_size, gt=0, lt=201):
        raise HTTPException(status_code=400, detail="Invalid page_size (must be 1-200)")

    # Validate sort params
    if sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by column. Must be one of: {', '.join(SORTABLE_COLUMNS)}",
        )

    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order (must be 'asc' or 'desc')")

    # Build WHERE clause
    where_clauses = []
    params = {}

    if search is not None and search.strip():
        where_clauses.append("LOWER(player_name) LIKE LOWER(:search)")
        params["search"] = f"%{search.strip()}%"

    if position is not None:
        if position not in ALLOWED_POSITIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid position. Must be one of: {', '.join(ALLOWED_POSITIONS)}",
            )
        where_clauses.append("position = :position")
        params["position"] = position

    if pos_group is not None:
        if pos_group not in ALLOWED_POS_GROUPS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pos_group. Must be one of: {', '.join(ALLOWED_POS_GROUPS)}",
            )
        where_clauses.append("pos_group = :pos_group")
        params["pos_group"] = pos_group

    if server is not None:
        if server not in ALLOWED_SERVERS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid server. Must be one of: {', '.join(ALLOWED_SERVERS)}",
            )
        where_clauses.append("server = :server")
        params["server"] = server

    if console is not None:
        if console not in ALLOWED_CONSOLES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid console. Must be one of: {', '.join(ALLOWED_CONSOLES)}",
            )
        where_clauses.append("console = :console")
        params["console"] = console

    if not show_rostered:
        where_clauses.append("is_rostered = false")

    if last_season_id is not None:
        where_clauses.append("last_season_id = :last_season_id")
        params["last_season_id"] = last_season_id

    if last_league_id is not None:
        if last_league_id not in ALLOWED_LEAGUE_IDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid last_league_id. Must be one of: {', '.join(map(str, ALLOWED_LEAGUE_IDS))}",
            )
        where_clauses.append("last_league_id = :last_league_id")
        params["last_league_id"] = last_league_id

    # Build WHERE string
    where_str = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_query = text(f"SELECT COUNT(*) FROM api.bidding_package WHERE {where_str}")
    count_result = await session.execute(count_query, params)
    total = count_result.scalar() or 0

    # Build ORDER BY with NULL handling
    null_order = "NULLS LAST" if sort_order == "desc" else "NULLS FIRST"
    order_str = f"{sort_by} {sort_order.upper()} {null_order}"

    # Add pagination params
    offset = (page_number - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    # Main query
    data_query = text(f"""
        SELECT
            signup_id,
            player_id,
            player_name,
            position,
            pos_group,
            status,
            server,
            console,
            signup_timestamp,
            is_rostered,
            current_team_id,
            current_team_name,
            last_season_id,
            last_league_id,
            last_league_name,
            last_pos_group,
            games_played,
            wins,
            losses,
            ot_losses,
            points,
            war_percentile,
            team_percentile,
            sos_percentile
        FROM api.bidding_package
        WHERE {where_str}
        ORDER BY {order_str}
        LIMIT :limit OFFSET :offset
    """)

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    # Transform to response schema
    data = []
    for row in rows:
        data.append(
            BiddingPackageData(
                signup_id=row.signup_id,
                player_id=row.player_id,
                player_name=row.player_name,
                position=row.position,
                pos_group=row.pos_group,
                status=row.status,
                server=row.server,
                console=row.console,
                signup_timestamp=row.signup_timestamp,
                is_rostered=row.is_rostered,
                current_team_id=row.current_team_id,
                current_team_name=row.current_team_name,
                last_season_id=row.last_season_id,
                last_league_id=row.last_league_id,
                last_league_name=row.last_league_name,
                last_pos_group=row.last_pos_group,
                games_played=row.games_played,
                wins=row.wins,
                losses=row.losses,
                ot_losses=row.ot_losses,
                points=row.points,
                war_percentile=row.war_percentile,
                team_percentile=row.team_percentile,
                sos_percentile=row.sos_percentile,
            )
        )

    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return Pagination(
        data=data,
        page=page_number,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        last_updated="N/A",  # View doesn't track last_updated
    )


# League ID to name mapping
LEAGUE_NAMES = {
    37: "NHL",
    38: "AHL",
    39: "CHL",
    84: "ECHL",
    112: "NCAA",
}


@router.get("/player/{player_id}", response_model=BiddingPackagePlayerDetail)
async def get_bidding_package_player(
    player_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_bidding_package),
):
    """
    Get detailed player information including all historical seasons.

    Requires one-time Bidding Package purchase.

    Args:
        player_id: The player's unique ID

    Returns:
        Player basic info and list of historical season stats with ratings.
    """
    # Get basic player info from bidding package
    player_query = text("""
        SELECT
            signup_id,
            player_id,
            player_name,
            position,
            pos_group,
            status,
            server,
            console,
            signup_timestamp,
            is_rostered,
            current_team_id,
            current_team_name
        FROM api.bidding_package
        WHERE player_id = :player_id
        LIMIT 1
    """)

    player_result = await session.execute(player_query, {"player_id": player_id})
    player_row = player_result.fetchone()

    if not player_row:
        raise HTTPException(status_code=404, detail="Player not found in bidding package")

    # Build player basic info
    player_info = PlayerBasicInfo(
        player_id=player_row.player_id,
        player_name=player_row.player_name,
        position=player_row.position,
        pos_group=player_row.pos_group,
        signup_id=player_row.signup_id,
        status=player_row.status,
        server=player_row.server,
        console=player_row.console,
        signup_timestamp=player_row.signup_timestamp,
        is_rostered=player_row.is_rostered,
        current_team_id=player_row.current_team_id,
        current_team_name=player_row.current_team_name,
    )

    # Determine if player is a goalie based on their current position
    is_goalie = player_row.pos_group == "G"

    seasons = []

    if is_goalie:
        # Query goalie stats
        goalie_query = text("""
            WITH goalie_seasons AS (
                SELECT DISTINCT
                    stats.season_id,
                    stats.league_id,
                    stats.game_type_id,
                    stats.player_id,
                    stats.pos_group
                FROM agg.agg_goalie_season_stats stats
                WHERE stats.player_id = :player_id
                  AND stats.game_type_id = 1
                  AND stats.league_id IN (37, 38, 39, 84, 112)
            )
            SELECT
                gs.season_id,
                gs.league_id,
                gs.game_type_id,
                gs.pos_group,

                -- Team info from rosters
                r.team_id,
                t.team_name,
                r.contract,

                -- Basic goalie stats
                stats.gp as games_played,
                stats.win as wins,
                stats.loss as losses,
                stats.otl as ot_losses,
                stats.toi,
                stats.shots_against,
                stats.saves,
                stats.goals_against,
                stats.sv_pct as save_pct,
                stats.gaa,
                stats.shutouts,

                -- Goalie GAR metrics
                gar.gsax,
                gar.gsaa,
                gar.gsax_per_60_percentile as gsax_percentile,
                gar.sv_pct_percentile as save_pct_percentile,
                gar.gaa_percentile,

                -- SOS metrics
                sos.teammate_rating,
                sos.opponent_rating

            FROM goalie_seasons gs

            LEFT JOIN agg.agg_goalie_season_stats stats
                ON gs.player_id = stats.player_id
                AND gs.season_id = stats.season_id
                AND gs.league_id = stats.league_id
                AND gs.game_type_id = stats.game_type_id
                AND gs.pos_group = stats.pos_group

            LEFT JOIN gar.gar_goalie_season gar
                ON gs.player_id = gar.player_id
                AND gs.season_id = gar.season_id
                AND gs.league_id = gar.league_id
                AND gs.game_type_id = gar.game_type_id
                AND gs.pos_group = gar.pos_group

            LEFT JOIN sos.sos_player_season sos
                ON gs.player_id = sos.player_id
                AND gs.season_id = sos.season_id
                AND gs.league_id = sos.league_id
                AND gs.game_type_id = sos.game_type_id
                AND gs.pos_group = sos.pos_group

            LEFT JOIN staging.stg_rosters r
                ON gs.player_id = r.player_id
                AND gs.season_id = r.season_id
                AND gs.league_id = r.league_id

            LEFT JOIN staging.stg_teams t
                ON r.team_id = t.team_id
                AND r.season_id = t.season_id
                AND r.league_id = t.league_id

            ORDER BY gs.season_id DESC, gs.league_id ASC
        """)

        goalie_result = await session.execute(goalie_query, {"player_id": player_id})
        goalie_rows = goalie_result.fetchall()

        for row in goalie_rows:
            seasons.append(
                PlayerSeasonStats(
                    season_id=row.season_id,
                    league_id=int(row.league_id),
                    league_name=LEAGUE_NAMES.get(int(row.league_id)),
                    game_type_id=row.game_type_id,
                    pos_group=row.pos_group,
                    team_id=row.team_id,
                    team_name=row.team_name,
                    contract=row.contract,
                    games_played=row.games_played,
                    wins=row.wins,
                    losses=row.losses,
                    ot_losses=row.ot_losses,
                    toi=float(row.toi) if row.toi else None,
                    # Goalie-specific stats
                    shots_against=int(row.shots_against) if row.shots_against else None,
                    saves=int(row.saves) if row.saves else None,
                    goals_against=int(row.goals_against) if row.goals_against else None,
                    save_pct=float(row.save_pct) if row.save_pct else None,
                    gaa=float(row.gaa) if row.gaa else None,
                    shutouts=int(row.shutouts) if row.shutouts else None,
                    gsax=float(row.gsax) if row.gsax else None,
                    gsaa=float(row.gsaa) if row.gsaa else None,
                    # Goalie percentiles
                    save_pct_percentile=float(row.save_pct_percentile) if row.save_pct_percentile else None,
                    gaa_percentile=float(row.gaa_percentile) if row.gaa_percentile else None,
                    gsax_percentile=float(row.gsax_percentile) if row.gsax_percentile else None,
                    teammate_rating=float(row.teammate_rating) if row.teammate_rating else None,
                    opponent_rating=float(row.opponent_rating) if row.opponent_rating else None,
                )
            )
    else:
        # Query skater stats
        skater_query = text("""
            WITH player_seasons AS (
                SELECT DISTINCT
                    stats.season_id,
                    stats.league_id,
                    stats.game_type_id,
                    stats.player_id,
                    stats.pos_group
                FROM agg.agg_player_season_stats stats
                WHERE stats.player_id = :player_id
                  AND stats.game_type_id = 1
                  AND stats.league_id IN (37, 38, 39, 84, 112)
            )
            SELECT
                ps.season_id,
                ps.league_id,
                ps.game_type_id,
                ps.pos_group,

                -- Team info from rosters
                r.team_id,
                t.team_name,
                r.contract,

                -- Basic stats from agg schema
                stats.gp as games_played,
                stats.win as wins,
                stats.loss as losses,
                stats.otl as ot_losses,
                stats.points,
                stats.goals,
                stats.assists,
                stats.plus_minus,
                stats.toi,
                stats.shots,
                stats.hits,
                stats.blocks,
                stats.takeaways,
                stats.interceptions,
                stats.giveaways,
                stats.pim,

                -- GAR metrics
                gar.expected_goals,
                gar.expected_assists,
                gar.goals_above_expected,
                gar.assists_above_expected,
                gar.offensive_gar,
                gar.defensive_gar,
                gar.total_gar,
                gar.gar_per_60_percentile as war_percentile,
                gar.off_per_60_percentile as offense_percentile,
                gar.def_per_60_percentile as defense_percentile,

                -- SOS metrics
                sos.teammate_rating,
                sos.opponent_rating

            FROM player_seasons ps

            LEFT JOIN agg.agg_player_season_stats stats
                ON ps.player_id = stats.player_id
                AND ps.season_id = stats.season_id
                AND ps.league_id = stats.league_id
                AND ps.game_type_id = stats.game_type_id
                AND ps.pos_group = stats.pos_group

            LEFT JOIN gar.gar_player_season gar
                ON ps.player_id = gar.player_id
                AND ps.season_id = gar.season_id
                AND ps.league_id = gar.league_id
                AND ps.game_type_id = gar.game_type_id
                AND ps.pos_group = gar.pos_group

            LEFT JOIN sos.sos_player_season sos
                ON ps.player_id = sos.player_id
                AND ps.season_id = sos.season_id
                AND ps.league_id = sos.league_id
                AND ps.game_type_id = sos.game_type_id
                AND ps.pos_group = sos.pos_group

            LEFT JOIN staging.stg_rosters r
                ON ps.player_id = r.player_id
                AND ps.season_id = r.season_id
                AND ps.league_id = r.league_id

            LEFT JOIN staging.stg_teams t
                ON r.team_id = t.team_id
                AND r.season_id = t.season_id
                AND r.league_id = t.league_id

            ORDER BY ps.season_id DESC, ps.league_id ASC
        """)

        skater_result = await session.execute(skater_query, {"player_id": player_id})
        skater_rows = skater_result.fetchall()

        for row in skater_rows:
            seasons.append(
                PlayerSeasonStats(
                    season_id=row.season_id,
                    league_id=int(row.league_id),
                    league_name=LEAGUE_NAMES.get(int(row.league_id)),
                    game_type_id=row.game_type_id,
                    pos_group=row.pos_group,
                    team_id=row.team_id,
                    team_name=row.team_name,
                    contract=row.contract,
                    games_played=row.games_played,
                    wins=row.wins,
                    losses=row.losses,
                    ot_losses=row.ot_losses,
                    points=row.points,
                    goals=row.goals,
                    assists=row.assists,
                    plus_minus=row.plus_minus,
                    toi=float(row.toi) if row.toi else None,
                    shots=row.shots,
                    hits=row.hits,
                    blocks=row.blocks,
                    takeaways=row.takeaways,
                    interceptions=row.interceptions,
                    giveaways=row.giveaways,
                    pim=row.pim,
                    expected_goals=float(row.expected_goals) if row.expected_goals else None,
                    expected_assists=float(row.expected_assists) if row.expected_assists else None,
                    goals_above_expected=float(row.goals_above_expected) if row.goals_above_expected else None,
                    assists_above_expected=float(row.assists_above_expected) if row.assists_above_expected else None,
                    offensive_gar=float(row.offensive_gar) if row.offensive_gar else None,
                    defensive_gar=float(row.defensive_gar) if row.defensive_gar else None,
                    total_gar=float(row.total_gar) if row.total_gar else None,
                    war_percentile=float(row.war_percentile) if row.war_percentile else None,
                    offense_percentile=float(row.offense_percentile) if row.offense_percentile else None,
                    defense_percentile=float(row.defense_percentile) if row.defense_percentile else None,
                    teammate_rating=float(row.teammate_rating) if row.teammate_rating else None,
                    opponent_rating=float(row.opponent_rating) if row.opponent_rating else None,
                )
            )

    return BiddingPackagePlayerDetail(
        player=player_info,
        seasons=seasons,
    )
