from datetime import datetime
from sqlalchemy import BigInteger, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class TeamSOS(Base):
    __tablename__ = "team_sos"
    __table_args__ = {"schema": "api"}

    # Composite primary key
    season_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    league_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    game_type_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    week_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    game_dow: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    team_id: Mapped[int | None] = mapped_column(BigInteger, primary_key=True, nullable=True)

    # Team info
    team_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Record
    win: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    loss: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    otl: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # SOS metrics
    teammate_win_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    opponent_win_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    teammate_rating: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    opponent_rating: Mapped[float | None] = mapped_column(Numeric, nullable=True)


class TeamCard(Base):
    __tablename__ = "teams_page"
    __table_args__ = {"schema": "api"}

    # Composite primary key
    season_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    league_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    game_type_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    team_id: Mapped[int | None] = mapped_column(BigInteger, primary_key=True, nullable=True)

    # Team info
    team_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    team_full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    team_color: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Record
    wins: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ot_losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Percentiles
    offense_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    defense_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    goalie_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    opponents_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    overall_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    overall_tier: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats
    total_goals: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    total_goals_against: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    total_xg: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    goals_per_60: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    total_opponent_xg: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    ga_per_60: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # Last updated
    last_updated: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    # Data versioning for subscription tiers
    data_week_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
