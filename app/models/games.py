from datetime import datetime, date
from sqlalchemy import BigInteger, Integer, Numeric, String, Text, TIMESTAMP, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class GamesPage(Base):
    """api.games_page — one row per game for the Games list page."""
    __tablename__ = "games_page"
    __table_args__ = {"schema": "api"}

    game_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    season_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    league_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    game_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    week_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    game_datetime: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    game_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Home
    home_team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    home_team_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    home_team_full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    home_team_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Away
    away_team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    away_team_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    away_team_full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    away_team_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Result / status
    is_overtime: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_forfeit: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_final: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    winner: Mapped[str | None] = mapped_column(Text, nullable=True)  # 'home' | 'away' | 'tie' | 'scheduled'

    last_updated: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    data_week_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class GameTeamStats(Base):
    """api.game_team_stats_page — per-team box totals + period scoring + team GAR."""
    __tablename__ = "game_team_stats_page"
    __table_args__ = {"schema": "api"}

    game_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    opponent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    team_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_team_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    team_color: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_home: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    team_wins: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    team_losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    team_otl: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    p1g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p2g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    p3g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    otg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_overtime: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    win: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss: Mapped[int | None] = mapped_column(Integer, nullable=True)
    otl: Mapped[int | None] = mapped_column(Integer, nullable=True)

    goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    toa: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fol: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ppg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ppa: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    takeaways: Mapped[int | None] = mapped_column(Integer, nullable=True)
    giveaways: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interceptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pk_clears: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passes_att: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)

    total_gar: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    offensive_gar: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    defensive_gar: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    total_xg: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    opponent_xg: Mapped[float | None] = mapped_column(Numeric, nullable=True)


class GameSkaterStats(Base):
    """api.game_skater_stats_page — per-skater game line + GAR."""
    __tablename__ = "game_skater_stats_page"
    __table_args__ = {"schema": "api"}

    game_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    player_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    position: Mapped[str | None] = mapped_column(String(8), nullable=True)
    pos_group: Mapped[str | None] = mapped_column(String(4), nullable=True)

    toi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plus_minus: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    takeaways: Mapped[int | None] = mapped_column(Integer, nullable=True)
    giveaways: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    interceptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pim: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ppg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gwg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fow: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fol: Mapped[int | None] = mapped_column(Integer, nullable=True)

    total_gar: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    offensive_gar: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    defensive_gar: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    xg: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    xa: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    ovr: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    off_rating: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    def_rating: Mapped[float | None] = mapped_column(Numeric, nullable=True)


class GameGoalieStats(Base):
    """api.game_goalie_stats_page — per-goalie game line + GAR."""
    __tablename__ = "game_goalie_stats_page"
    __table_args__ = {"schema": "api"}

    game_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    player_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    toi: Mapped[int | None] = mapped_column(Integer, nullable=True)
    shots_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    saves: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sv_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gaa: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    shutouts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gsax: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gsaa: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    ovr: Mapped[float | None] = mapped_column(Numeric, nullable=True)
