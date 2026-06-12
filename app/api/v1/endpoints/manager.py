"""
Manager Tools Endpoints

Endpoints for GM-focused tools (requires Manager Tools subscription).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_manager_tools
from app.database.session import get_db
from app.models.users import User
from app.schemas.common import Pagination
from app.schemas.manager import ContractValueData
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
    "pos_group",
    "team_name",
    "wins",
    "losses",
    "points",
    "contract",
    "fair_contract",
    "surplus_value",
    "total_gar",
    "gar_per_60",
    "war_percentile",
    "tier_rank",
    "contract_rank",
    "position_contract_rank",
]

ALLOWED_POS_GROUPS = ["F", "D", "G", "C", "W"]
ALLOWED_LEAGUE_IDS = [37, 38, 39, 84, 112]  # LGHL, LGAHL, LGCHL, LGECHL, LGNCAA
ALLOWED_GAME_TYPE_IDS = [1, 2]

# ============================================
# ENDPOINTS
# ============================================


@router.get("/contract-values", response_model=Pagination[ContractValueData])
async def get_contract_values(
    season_id: int,
    league_id: int,
    game_type_id: int = 1,
    search: str | None = None,
    pos_group: str | None = None,
    rostered_only: bool = False,
    page_number: int = 1,
    page_size: int = 50,
    sort_by: str = "surplus_value",
    sort_order: str = "desc",
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_manager_tools),
):
    """
    Get paginated contract value data with filtering and sorting.

    Requires Manager Tools subscription.

    Compares actual contracts against GAR-based fair value.
    surplus_value = fair_contract - contract (positive = underpaid).

    Args:
        season_id: Season to query
        league_id: League ID (37=LGHL, 38=LGAHL, 39=LGCHL, 84=LGECHL, 112=LGNCAA)
        game_type_id: 1=Regular season, 2=Playoffs (default 1)
        search: Search player names (case-insensitive partial match)
        pos_group: Filter by position group (F, D, G, C, W)
        rostered_only: Only include players with a contract (default False)
        page_number: Page number (default 1)
        page_size: Items per page (default 50, max 200)
        sort_by: Column to sort by (default: surplus_value)
        sort_order: Sort direction (asc/desc, default: desc)

    Returns:
        Paginated contract value data.
    """
    # Validate filters
    if not validate_param("season_id", season_id, gt=0):
        raise HTTPException(status_code=400, detail="Invalid season_id")

    if not validate_param("league_id", league_id, allowed_values=ALLOWED_LEAGUE_IDS):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid league_id. Must be one of: {', '.join(map(str, ALLOWED_LEAGUE_IDS))}",
        )

    if not validate_param("game_type_id", game_type_id, allowed_values=ALLOWED_GAME_TYPE_IDS):
        raise HTTPException(status_code=400, detail="Invalid game_type_id (must be 1 or 2)")

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
    where_clauses = [
        "season_id = :season_id",
        "league_id = :league_id",
        "game_type_id = :game_type_id",
    ]
    params: dict = {
        "season_id": season_id,
        "league_id": league_id,
        "game_type_id": game_type_id,
    }

    if search is not None and search.strip():
        where_clauses.append("LOWER(player_name) LIKE LOWER(:search)")
        params["search"] = f"%{search.strip()}%"

    if pos_group is not None:
        if pos_group not in ALLOWED_POS_GROUPS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pos_group. Must be one of: {', '.join(ALLOWED_POS_GROUPS)}",
            )
        where_clauses.append("pos_group = :pos_group")
        params["pos_group"] = pos_group

    if rostered_only:
        where_clauses.append("contract IS NOT NULL")

    where_str = " AND ".join(where_clauses)

    # Get total count and last updated timestamp
    count_query = text(f"""
        SELECT COUNT(*), MAX(last_updated)
        FROM api.contract_values_page
        WHERE {where_str}
    """)
    count_result = await session.execute(count_query, params)
    count_row = count_result.fetchone()
    total = count_row[0] or 0
    latest_update = count_row[1]

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
            player_id,
            player_name,
            pos_group,
            team_name,
            team_color,
            wins,
            losses,
            ot_losses,
            goals,
            assists,
            points,
            contract,
            fair_contract,
            surplus_value,
            total_gar,
            gar_per_60,
            war_percentile,
            contract_tier,
            tier_rank,
            contract_rank,
            position_contract_rank,
            salary_cap
        FROM api.contract_values_page
        WHERE {where_str}
        ORDER BY {order_str}
        LIMIT :limit OFFSET :offset
    """)

    result = await session.execute(data_query, params)
    rows = result.fetchall()

    # Transform to response schema
    data = [
        ContractValueData(
            player_id=row.player_id,
            player_name=row.player_name,
            pos_group=row.pos_group,
            team_name=row.team_name,
            team_color=row.team_color,
            wins=row.wins,
            losses=row.losses,
            ot_losses=row.ot_losses,
            goals=row.goals,
            assists=row.assists,
            points=row.points,
            contract=row.contract,
            fair_contract=row.fair_contract,
            surplus_value=row.surplus_value,
            total_gar=row.total_gar,
            gar_per_60=row.gar_per_60,
            war_percentile=row.war_percentile,
            contract_tier=row.contract_tier,
            tier_rank=row.tier_rank,
            contract_rank=row.contract_rank,
            position_contract_rank=row.position_contract_rank,
            salary_cap=row.salary_cap,
        )
        for row in rows
    ]

    # Calculate pagination metadata
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    # Format last updated timestamp
    if latest_update:
        last_updated = latest_update.strftime("%b %d, %Y %I:%M %p")
    else:
        last_updated = "N/A"

    return Pagination(
        data=data,
        page=page_number,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        last_updated=last_updated,
    )
