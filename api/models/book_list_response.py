"""
API response models.
"""
from typing import List
from pydantic import BaseModel, Field
from api.models.book_response import BookResponse


class BooksListResponse(BaseModel):
    """Response model for list of books with pagination."""
    
    books: List[BookResponse] = Field(..., description="List of books")
    total: int = Field(..., description="Total number of books")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "books": [
                    {
                        "id": "507f1f77bcf86cd799439011",
                        "title": "A Light in the Attic",
                        "category": "Poetry",
                        "price_incl_tax": 51.77,
                        "rating": 3
                    }
                ],
                "total": 1000,
                "page": 1,
                "page_size": 20,
                "total_pages": 50
            }
        }

