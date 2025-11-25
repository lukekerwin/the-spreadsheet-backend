from pydantic import BaseModel


class TeamSOSData(BaseModel):
    season_id: int
    league_id: int
    game_type_id: int
    week_id: int
    game_dow: int
    team_id: int
    team_name: str
    win: int | None
    loss: int | None
    otl: int | None
    teammate_win_pct: float | None
    opponent_win_pct: float | None
    teammate_rating: float | None
    opponent_rating: float | None

    class Config:
        from_attributes = True
