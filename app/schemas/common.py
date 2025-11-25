"""
Common Schemas

Shared Pydantic models used across API responses.
Uses camelCase for JSON serialization following REST API conventions.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Generic, TypeVar, List

T = TypeVar("T")

# ============================================
# ITEM SCHEMA
# ============================================

class Item(BaseModel):
    """Generic item with label and value for card stats."""
    label: str
    value: int | float | str

# ============================================
# PAGINATION SCHEMA
# ============================================

class Pagination(BaseModel, Generic[T]):
    """
    Generic pagination response wrapper.
    
    Uses camelCase for JSON serialization (REST API convention).
    Python code uses snake_case internally, but serializes to camelCase.
    """
    model_config = ConfigDict(populate_by_name=True, by_alias=True)
    
    data: List[T]
    page: int = Field(serialization_alias="pageNumber")
    page_size: int = Field(serialization_alias="pageSize")
    total: int
    total_pages: int = Field(serialization_alias="totalPages")
    last_updated: str = Field(serialization_alias="lastUpdated")
