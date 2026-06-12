"""
Manager Tools Schemas

Pydantic models for manager tools responses (contract values, etc.).
"""

from pydantic import BaseModel


class ContractValueData(BaseModel):
    """Single row of contract value data."""

    player_id: int
    player_name: str | None
    pos_group: str | None
    team_name: str | None
    team_color: str | None
    wins: int | None
    losses: int | None
    ot_losses: int | None
    goals: int | None
    assists: int | None
    points: int | None
    contract: int | None
    fair_contract: int | None
    surplus_value: int | None
    total_gar: float | None
    gar_per_60: float | None
    war_percentile: float | None
    contract_tier: str | None
    tier_rank: int | None
    contract_rank: int | None
    position_contract_rank: int | None
    salary_cap: int | None
