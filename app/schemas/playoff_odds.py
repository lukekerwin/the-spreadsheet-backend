"""
Pydantic schemas for playoff odds API responses
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Optional


class SeedingProbabilities(BaseModel):
    """Probabilities for each playoff seed (1-8)"""
    seed_1: float = Field(..., alias='seed_1_prob', description='Probability of 1st seed')
    seed_2: float = Field(..., alias='seed_2_prob', description='Probability of 2nd seed')
    seed_3: float = Field(..., alias='seed_3_prob', description='Probability of 3rd seed')
    seed_4: float = Field(..., alias='seed_4_prob', description='Probability of 4th seed')
    seed_5: float = Field(..., alias='seed_5_prob', description='Probability of 5th seed')
    seed_6: float = Field(..., alias='seed_6_prob', description='Probability of 6th seed')
    seed_7: float = Field(..., alias='seed_7_prob', description='Probability of 7th seed')
    seed_8: float = Field(..., alias='seed_8_prob', description='Probability of 8th seed')

    class Config:
        populate_by_name = True


class PlayoffOddsResponse(BaseModel):
    """Response model for playoff odds data"""

    season_id: int = Field(..., description='Season ID')
    league_id: int = Field(..., description='League ID')
    team_id: int = Field(..., description='Team ID')
    full_team_name: str = Field(..., description='Full team name (e.g., "Toronto Maple Leafs")')
    team_name: str = Field(..., description='Short team name (e.g., "Maple Leafs")')
    conference_id: int | None = Field(None, description='Conference ID (1=East, 2=West)')

    # Current standings
    points: int = Field(..., description='Current points')
    wins: int = Field(..., description='Current wins')
    losses: int = Field(..., description='Current losses')
    ot_losses: int = Field(..., description='Current OT losses')
    games_remaining: int = Field(..., description='Games remaining in season')

    # Playoff probability
    playoff_odds: float = Field(..., description='Probability of making playoffs (0-100)')

    # Seeding probabilities (flexible for any number of seeds)
    seed_probabilities: Optional[Dict[str, float]] = Field(None, description='Seed probabilities as JSON (all seeds)')
    
    # Legacy seeding probabilities (for backward compatibility, seeds 1-8 only)
    seed_1_prob: float = Field(..., description='Probability of 1st seed')
    seed_2_prob: float = Field(..., description='Probability of 2nd seed')
    seed_3_prob: float = Field(..., description='Probability of 3rd seed')
    seed_4_prob: float = Field(..., description='Probability of 4th seed')
    seed_5_prob: float = Field(..., description='Probability of 5th seed')
    seed_6_prob: float = Field(..., description='Probability of 6th seed')
    seed_7_prob: float = Field(..., description='Probability of 7th seed')
    seed_8_prob: float = Field(..., description='Probability of 8th seed')

    # Metadata
    num_simulations: int = Field(..., description='Number of simulations run')
    last_updated: datetime = Field(..., description='Last updated timestamp')

    class Config:
        from_attributes = True
