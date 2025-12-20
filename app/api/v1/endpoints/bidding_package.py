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
