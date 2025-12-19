from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BiddingPackageData(BaseModel):
    """Individual bidding package row - signup with last season stats"""

    model_config = ConfigDict(populate_by_name=True)

    # Signup info
    signup_id: str
    player_id: int
    player_name: str | None
    position: str
    pos_group: str
    status: str | None
    server: str | None
    console: str | None
    signup_timestamp: datetime | None

    # Roster status
    is_rostered: bool
    current_team_id: int | None = None
    current_team_name: str | None = None

    # Last season stats
    last_season_id: int | None = None
    last_league_id: int | None = None
    last_league_name: str | None = None
    last_pos_group: str | None = None
    games_played: int | None = None
    wins: int | None = None
    losses: int | None = None
    ot_losses: int | None = None
    points: int | None = None

    # Ratings (0-1 scale, frontend multiplies by 100)
    war_percentile: float | None = None
    team_percentile: float | None = None
    sos_percentile: float | None = None
