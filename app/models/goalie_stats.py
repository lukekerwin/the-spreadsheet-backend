from sqlalchemy import BigInteger, Integer, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base
from datetime import datetime


class GoalieStatsPage(Base):
    __tablename__ = "goalie_stats_page"
    __table_args__ = {"schema": "api"}

    # Composite Primary Key
    season_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    league_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pos_group: Mapped[str] = mapped_column(String(10), primary_key=True)

    # Player Info
    player_name: Mapped[str | None] = mapped_column(String, nullable=True)
    team_name: Mapped[str | None] = mapped_column(String, nullable=True)
    contract: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Record
    win: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss: Mapped[int | None] = mapped_column(Integer, nullable=True)
    otl: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Goalie Stats
    shots_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xsh: Mapped[float | None] = mapped_column(Float, nullable=True)
    shots_prevented: Mapped[float | None] = mapped_column(Float, nullable=True)
    goals_against: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xga: Mapped[float | None] = mapped_column(Float, nullable=True)
    gsax: Mapped[float | None] = mapped_column(Float, nullable=True)
    gsaa: Mapped[float | None] = mapped_column(Float, nullable=True)
    shutouts: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Ratings (percentiles 0-100)
    overall_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    teammate_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    opponent_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
