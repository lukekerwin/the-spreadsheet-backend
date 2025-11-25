from pydantic import BaseModel, Field, ConfigDict


class TeamFilterOption(BaseModel):
    """Team filter option for dropdown"""
    team_name: str


class PlayerStatsData(BaseModel):
    """Individual player statistics row"""

    model_config = ConfigDict(populate_by_name=True)

    # IDs (for filtering/identification)
    season_id: int
    league_id: int
    game_type_id: int
    player_id: int
    pos_group: str

    # General
    player_name: str
    team_name: str
    win: int
    loss: int
    otl: int
    contract: float

    # Offense
    points: int
    goals: int
    assists: int
    plus_minus: int
    xG: float = Field(validation_alias="xg")
    xA: float = Field(validation_alias="xa")
    GaX: float = Field(validation_alias="gax")
    AaX: float = Field(validation_alias="aax")
    iOFF: float = Field(validation_alias="ioff")  # Will be multiplied by 100 in endpoint
    off_gar: float

    # Defense
    interceptions: int
    takeaways: int
    blocks: int
    iDEF: float = Field(validation_alias="idef")  # Will be multiplied by 100 in endpoint
    def_gar: float

    # Ratings
    overall_rating: float | None
    offense_rating: float | None
    defense_rating: float | None
    teammate_rating: float | None
    opponent_rating: float | None
