from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    """Pagination metadata for paginated responses"""

    current_page: int = Field(..., description="Current page number (1-indexed)")
    total_pages: int = Field(..., description="Total number of pages")
    total_entries: int = Field(..., description="Total number of entries across all pages")
    page_size: int = Field(..., description="Number of entries per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_page: Optional[int] = Field(None, description="Next page number if available")
    previous_page: Optional[int] = Field(None, description="Previous page number if available")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""

    model_config = ConfigDict(from_attributes=True)

    data: List[T] = Field(..., description="List of items for the current page")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")
