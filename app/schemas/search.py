from pydantic import BaseModel, ConfigDict

class SearchResultItem(BaseModel):
    id: int
    name: str

class SearchResult(BaseModel):
    results: list[SearchResultItem]