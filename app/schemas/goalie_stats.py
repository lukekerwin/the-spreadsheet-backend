from pydantic import BaseModel, Field, ConfigDict


class TeamFilterOption(BaseModel):
    """Team filter option for dropdown"""
    team_name: str


class GoalieStatsData(BaseModel):
    """Individual goalie statistics row"""

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

    # Goalie Stats
    shots_against: int
    xSH: float = Field(validation_alias="xsh")
    shots_prevented: float
    goals_against: int
    xGA: float = Field(validation_alias="xga")
    GSAX: float = Field(validation_alias="gsax")
    GSAA: float = Field(validation_alias="gsaa")
    shutouts: int

    # Ratings
    overall_rating: float | None
    teammate_rating: float | None
    opponent_rating: float | None
