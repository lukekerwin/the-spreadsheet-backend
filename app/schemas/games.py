"""
Games Schemas

Response models for the Games list page. camelCase serialization (REST convention).
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Camel(BaseModel):
    """Base that serializes snake_case fields as camelCase."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class TeamSide(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: Optional[int] = None
    name: Optional[str] = None
    full_name: Optional[str] = Field(default=None, serialization_alias="fullName")
    color: Optional[str] = None
    logo_path: Optional[str] = Field(default=None, serialization_alias="logoPath")
    score: Optional[int] = None


class GameRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    game_id: int = Field(serialization_alias="gameId")
    week_id: Optional[int] = Field(default=None, serialization_alias="weekId")
    game_datetime: Optional[datetime] = Field(default=None, serialization_alias="gameDatetime")
    home: TeamSide
    away: TeamSide
    winner: Optional[str] = None          # 'home' | 'away' | 'tie' | 'scheduled'
    is_overtime: bool = Field(default=False, serialization_alias="isOvertime")
    is_forfeit: bool = Field(default=False, serialization_alias="isForfeit")
    is_final: bool = Field(default=False, serialization_alias="isFinal")


class WeekOption(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    week_id: int = Field(serialization_alias="weekId")
    played: int
    scheduled: int


class DayOption(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: str                                   # ISO yyyy-mm-dd (filter value)
    label: str                                  # weekday name, e.g. "Tuesday"
    played: int


class GamesResponse(BaseModel):
    """Everything the Games page needs in one call: games + resolved filters + options."""
    model_config = ConfigDict(populate_by_name=True)
    data: List[GameRow]
    season_id: int = Field(serialization_alias="seasonId")
    league_id: int = Field(serialization_alias="leagueId")
    game_type_id: int = Field(serialization_alias="gameTypeId")
    week_id: int = Field(serialization_alias="weekId")
    game_date: Optional[str] = Field(default=None, serialization_alias="gameDate")  # resolved day
    seasons: List[int]                                            # available seasons, desc
    weeks: List[WeekOption]                                       # weeks for the resolved season
    days: List[DayOption]                                         # days (with results) in the resolved week
    total: int
    page_number: int = Field(serialization_alias="pageNumber")
    page_size: int = Field(serialization_alias="pageSize")
    total_pages: int = Field(serialization_alias="totalPages")
    last_updated: str = Field(serialization_alias="lastUpdated")


# ============================================
# GAME DETAIL
# ============================================

class TeamBreakdown(_Camel):
    team_id: int
    team_name: Optional[str] = None
    full_team_name: Optional[str] = None
    team_color: Optional[str] = None
    logo_path: Optional[str] = None
    is_home: bool = False
    score: Optional[int] = None
    team_wins: Optional[int] = None
    team_losses: Optional[int] = None
    team_otl: Optional[int] = None
    # explicit aliases: the camelCase generator would otherwise emit p1G/p2G/p3G
    p1g: int = Field(default=0, serialization_alias="p1g")
    p2g: int = Field(default=0, serialization_alias="p2g")
    p3g: int = Field(default=0, serialization_alias="p3g")
    otg: int = Field(default=0, serialization_alias="otg")
    is_overtime: bool = False
    win: Optional[int] = None
    loss: Optional[int] = None
    otl: Optional[int] = None
    goals: Optional[int] = None
    shots: Optional[int] = None
    hits: Optional[int] = None
    toa: Optional[int] = None
    fow: Optional[int] = None
    fol: Optional[int] = None
    pim: Optional[int] = None
    ppg: Optional[int] = None
    ppa: Optional[int] = None
    blocks: Optional[int] = None
    takeaways: Optional[int] = None
    giveaways: Optional[int] = None
    interceptions: Optional[int] = None
    pk_clears: Optional[int] = None
    shg: Optional[int] = None
    passes: Optional[int] = None
    passes_att: Optional[int] = None
    saves: Optional[int] = None
    total_gar: Optional[float] = None
    offensive_gar: Optional[float] = None
    defensive_gar: Optional[float] = None
    total_xg: Optional[float] = None
    opponent_xg: Optional[float] = None


class SkaterLine(_Camel):
    player_id: int
    player_name: Optional[str] = None
    team_id: Optional[int] = None
    position: Optional[str] = None
    pos_group: Optional[str] = None
    toi: Optional[int] = None
    points: Optional[int] = None
    goals: Optional[int] = None
    assists: Optional[int] = None
    plus_minus: Optional[int] = None
    shots: Optional[int] = None
    hits: Optional[int] = None
    takeaways: Optional[int] = None
    giveaways: Optional[int] = None
    blocks: Optional[int] = None
    interceptions: Optional[int] = None
    pim: Optional[int] = None
    ppg: Optional[int] = None
    shg: Optional[int] = None
    gwg: Optional[int] = None
    fow: Optional[int] = None
    fol: Optional[int] = None
    total_gar: Optional[float] = None
    offensive_gar: Optional[float] = None
    defensive_gar: Optional[float] = None
    xg: Optional[float] = None
    xa: Optional[float] = None
    ovr: Optional[float] = None
    off_rating: Optional[float] = None
    def_rating: Optional[float] = None


class GoalieLine(_Camel):
    player_id: int
    player_name: Optional[str] = None
    team_id: Optional[int] = None
    toi: Optional[int] = None
    shots_against: Optional[int] = None
    saves: Optional[int] = None
    goals_against: Optional[int] = None
    sv_pct: Optional[float] = None
    gaa: Optional[float] = None
    shutouts: Optional[int] = None
    gsax: Optional[float] = None
    gsaa: Optional[float] = None


class GameDetailResponse(_Camel):
    header: GameRow
    home_team: Optional[TeamBreakdown] = None
    away_team: Optional[TeamBreakdown] = None
    home_skaters: List[SkaterLine] = []
    away_skaters: List[SkaterLine] = []
    home_goalies: List[GoalieLine] = []
    away_goalies: List[GoalieLine] = []
