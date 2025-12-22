"""
Free tier snapshot models - mirrors of premium tables for weekly data.
Updated every Tuesday at 11:30 PM ET via scheduled job.
"""

from datetime import datetime
from sqlalchemy import BigInteger, Integer, Numeric, String, Text, TIMESTAMP, Float, DateTime, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base


class PlayerCardFree(Base):
    """Weekly snapshot of player cards for free users."""

    __tablename__ = "players_page_free"
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


class GoalieCardFree(Base):
    """Weekly snapshot of goalie cards for free users."""

    __tablename__ = "goalies_page_free"
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
    goals_against: Mapped[float | None] = mapped_column(Numeric, nullable=True)
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


class TeamCardFree(Base):
    """Weekly snapshot of team cards for free users."""

    __tablename__ = "teams_page_free"
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


class PlayerStatsPageFree(Base):
    """Weekly snapshot of player stats for free users."""

    __tablename__ = "players_stats_page_free"
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
    ioff: Mapped[float | None] = mapped_column(Float, nullable=True)
    off_gar: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Defense
    interceptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    takeaways: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blocks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    idef: Mapped[float | None] = mapped_column(Float, nullable=True)
    def_gar: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Ratings (percentiles 0-100)
    overall_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    offense_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    defense_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    teammate_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    opponent_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GoalieStatsPageFree(Base):
    """Weekly snapshot of goalie stats for free users."""

    __tablename__ = "goalie_stats_page_free"
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


class PlayoffOddsFree(Base):
    """Weekly snapshot of playoff odds for free users."""

    __tablename__ = "playoff_odds_free"
    __table_args__ = {"schema": "api"}

    season_id = Column(Integer, primary_key=True)
    league_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, primary_key=True)
    full_team_name = Column(String(200))
    team_name = Column(String(100))
    conference_id = Column(Integer)

    # Current standings
    points = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    ot_losses = Column(Integer)
    games_remaining = Column(Integer)

    # Playoff probability
    playoff_odds = Column(Numeric(5, 2))

    # Seeding probabilities (flexible JSONB for any number of seeds)
    seed_probabilities = Column(JSONB)

    # Legacy seeding probabilities (for backward compatibility, seeds 1-8 only)
    seed_1_prob = Column(Numeric(5, 2))
    seed_2_prob = Column(Numeric(5, 2))
    seed_3_prob = Column(Numeric(5, 2))
    seed_4_prob = Column(Numeric(5, 2))
    seed_5_prob = Column(Numeric(5, 2))
    seed_6_prob = Column(Numeric(5, 2))
    seed_7_prob = Column(Numeric(5, 2))
    seed_8_prob = Column(Numeric(5, 2))

    # Metadata
    num_simulations = Column(Integer)
    last_updated = Column(DateTime)


# Mapping from premium models to free models for easy lookup
MODEL_TIER_MAPPING = {
    "PlayerCard": ("PlayerCard", "PlayerCardFree"),
    "GoalieCard": ("GoalieCard", "GoalieCardFree"),
    "TeamCard": ("TeamCard", "TeamCardFree"),
    "PlayerStatsPage": ("PlayerStatsPage", "PlayerStatsPageFree"),
    "GoalieStatsPage": ("GoalieStatsPage", "GoalieStatsPageFree"),
    "PlayoffOdds": ("PlayoffOdds", "PlayoffOddsFree"),
}
