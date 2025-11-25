"""
SQLAlchemy model for playoff odds data
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PlayoffOdds(Base):
    """Playoff odds and seeding probabilities"""

    __tablename__ = 'playoff_odds'
    __table_args__ = {'schema': 'api'}

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
