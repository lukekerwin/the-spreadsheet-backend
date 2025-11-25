from sqlalchemy import BigInteger, Integer, String, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base
from datetime import datetime


class PlayerStatsPage(Base):
    __tablename__ = "players_stats_page"
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

    # Basic Stats
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plus_minus: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Advanced Offense
    xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    xa: Mapped[float | None] = mapped_column(Float, nullable=True)
    gax: Mapped[float | None] = mapped_column(Float, nullable=True)
    aax: Mapped[float | None] = mapped_column(Float, nullable=True)
    ioff: Mapped[float | None] = mapped_column(Float, nullable=True)  # Ratio 0.0-1.0
    off_gar: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Defense
    interceptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    takeaways: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    idef: Mapped[float | None] = mapped_column(Float, nullable=True)  # Ratio 0.0-1.0
    def_gar: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Ratings (percentiles 0-100)
    overall_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    offense_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    defense_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    teammate_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    opponent_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
