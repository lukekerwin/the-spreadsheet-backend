"""
Tier-based data routing utilities.

Routes queries to premium (live) or free (weekly snapshot) tables
based on user subscription status.
"""

from typing import Type
from app.models.users import User

# Premium models
from app.models.players import PlayerCard
from app.models.goalies import GoalieCard
from app.models.teams import TeamCard
from app.models.player_stats import PlayerStatsPage
from app.models.goalie_stats import GoalieStatsPage
from app.models.playoff_odds import PlayoffOdds

# Free tier snapshot models
from app.models.free_tier import (
    PlayerCardFree,
    GoalieCardFree,
    TeamCardFree,
    PlayerStatsPageFree,
    GoalieStatsPageFree,
    PlayoffOddsFree,
)


def get_player_card_model(user: User) -> Type[PlayerCard] | Type[PlayerCardFree]:
    """Get the appropriate player card model based on user tier."""
    if user.has_premium_access:
        return PlayerCard
    return PlayerCardFree


def get_goalie_card_model(user: User) -> Type[GoalieCard] | Type[GoalieCardFree]:
    """Get the appropriate goalie card model based on user tier."""
    if user.has_premium_access:
        return GoalieCard
    return GoalieCardFree


def get_team_card_model(user: User) -> Type[TeamCard] | Type[TeamCardFree]:
    """Get the appropriate team card model based on user tier."""
    if user.has_premium_access:
        return TeamCard
    return TeamCardFree


def get_player_stats_model(user: User) -> Type[PlayerStatsPage] | Type[PlayerStatsPageFree]:
    """Get the appropriate player stats model based on user tier."""
    if user.has_premium_access:
        return PlayerStatsPage
    return PlayerStatsPageFree


def get_goalie_stats_model(user: User) -> Type[GoalieStatsPage] | Type[GoalieStatsPageFree]:
    """Get the appropriate goalie stats model based on user tier."""
    if user.has_premium_access:
        return GoalieStatsPage
    return GoalieStatsPageFree


def get_playoff_odds_model(user: User) -> Type[PlayoffOdds] | Type[PlayoffOddsFree]:
    """Get the appropriate playoff odds model based on user tier."""
    if user.has_premium_access:
        return PlayoffOdds
    return PlayoffOddsFree
