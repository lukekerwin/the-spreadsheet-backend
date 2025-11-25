from datetime import datetime
from sqlalchemy import BigInteger, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class PlayerCard(Base):
    __tablename__ = "players_page"
    __table_args__ = {"schema": "api"}

    # Composite primary key
    season_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    league_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    game_type_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    player_id: Mapped[int | None] = mapped_column(BigInteger, primary_key=True, nullable=True)
    pos_group: Mapped[str | None] = mapped_column(String(10), primary_key=True, nullable=True)

    # Player info
    player_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Record
    wins: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ot_losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Contract and performance
    contract: Mapped[int | None] = mapped_column(Integer, nullable=True)
    war_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    tier: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Team info
    team_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    team_color: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stats
    points: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    goals: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    assists: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Advanced metrics
    war_offense_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    war_defense_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    team_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    sos_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # Individual offense
    ioff: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    xg: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    xa: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gf: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Individual defense
    idef: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    takeaways: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    interceptions: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ga: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Last updated
    last_updated: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    # Data versioning for subscription tiers
    data_week_id: Mapped[int | None] = mapped_column(Integer, nullable=True)