from pydantic import BaseModel


class SearchResultItem(BaseModel):
    id: int
    name: str


class SearchResult(BaseModel):
    results: list[SearchResultItem]
