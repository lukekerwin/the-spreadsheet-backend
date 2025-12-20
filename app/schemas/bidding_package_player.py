"""
Bidding Package Player Detail Schemas

Schemas for the player detail page showing historical stats and ratings.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PlayerSeasonStats(BaseModel):
    """Historical season stats for a player"""

    model_config = ConfigDict(populate_by_name=True)

    # Season info
    season_id: int
    league_id: int
    league_name: str | None = None
    game_type_id: int
    pos_group: str

    # Team info
    team_id: int | None = None
    team_name: str | None = None
    contract: int | None = None

    # Record
    games_played: int | None = None
    wins: int | None = None
    losses: int | None = None
    ot_losses: int | None = None

    # Basic stats (skaters)
    points: int | None = None
    goals: int | None = None
    assists: int | None = None
    plus_minus: int | None = None

    # Advanced stats (skaters)
    toi: float | None = None  # Time on ice in seconds
    shots: int | None = None
    hits: int | None = None
    blocks: int | None = None
    takeaways: int | None = None
    interceptions: int | None = None
    giveaways: int | None = None
    pim: int | None = None

    # Goalie stats
    shots_against: int | None = None
    saves: int | None = None
    goals_against: int | None = None
    save_pct: float | None = None
    gaa: float | None = None
    shutouts: int | None = None

    # Expected metrics (skaters)
    expected_goals: float | None = None
    expected_assists: float | None = None
    goals_above_expected: float | None = None
    assists_above_expected: float | None = None

    # GAR metrics (skaters)
    offensive_gar: float | None = None
    defensive_gar: float | None = None
    total_gar: float | None = None

    # Goalie advanced metrics
    gsax: float | None = None  # Goals Saved Above Expected
    gsaa: float | None = None  # Goals Saved Above Average

    # Ratings (0-1 scale)
    war_percentile: float | None = None
    offense_percentile: float | None = None
    defense_percentile: float | None = None
    teammate_rating: float | None = None
    opponent_rating: float | None = None
    # Goalie-specific percentiles
    save_pct_percentile: float | None = None
    gaa_percentile: float | None = None
    gsax_percentile: float | None = None


class PlayerBasicInfo(BaseModel):
    """Basic player information from signup"""

    model_config = ConfigDict(populate_by_name=True)

    # Player info
    player_id: int
    player_name: str | None = None
    position: str
    pos_group: str

    # Signup info
    signup_id: str
    status: str | None = None
    server: str | None = None
    console: str | None = None
    signup_timestamp: datetime | None = None

    # Current roster status
    is_rostered: bool
    current_team_id: int | None = None
    current_team_name: str | None = None


class BiddingPackagePlayerDetail(BaseModel):
    """Complete player detail for bidding package"""

    model_config = ConfigDict(populate_by_name=True)

    # Basic info
    player: PlayerBasicInfo

    # Historical seasons (newest first)
    seasons: list[PlayerSeasonStats]
