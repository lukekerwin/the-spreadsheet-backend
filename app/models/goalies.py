from datetime import datetime
from sqlalchemy import BigInteger, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class GoalieCard(Base):
    __tablename__ = "goalies_page"
    __table_args__ = {"schema": "api"}

    # Composite primary key
    season_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    league_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    game_type_id: Mapped[int | None] = mapped_column(Integer, primary_key=True, nullable=True)
    player_id: Mapped[int | None] = mapped_column(BigInteger, primary_key=True, nullable=True)

    # Player info
    player_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Record
    wins: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ot_losses: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Contract and performance
    contract: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    tier: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Team info
    team_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    team_color: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Header Stats
    save_pct: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gaa: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # Advanced metrics
    gsax_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    def_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    team_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    sos_percentile: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # Stats
    shots_against: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    goals_against: Mapped[int | None] = mapped_column(Numeric, nullable=True)
    xga: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gsax: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    shots_per_60: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    ga_per_60: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    xga_per_60: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    gsax_per_60: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    # Last updated
    last_updated: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    # Data versioning for subscription tiers
    data_week_id: Mapped[int | None] = mapped_column(Integer, nullable=True)