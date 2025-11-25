from pydantic import BaseModel, ConfigDict

from app.schemas.common import Item

class CardHeader(BaseModel):
    title: str
    subtitle: list[Item]

class CardBanner(BaseModel):
    overallPercentile: int | str
    tier: str | None
    logoPath: str | None

class CardData(BaseModel):
    header: CardHeader
    banner: CardBanner
    headerStats: list[Item]
    ratings: list[Item]
    stats: list[Item]
    teamColor: str