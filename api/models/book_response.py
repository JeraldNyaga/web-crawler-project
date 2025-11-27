from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class BookResponse(BaseModel):
    """Response model for book data."""
    
    id: str = Field(..., description="Book ID")
    url: str = Field(..., description="Book URL")
    title: str = Field(..., description="Book title")
    description: Optional[str] = Field(None, description="Book description")
    category: str = Field(..., description="Book category")
    price_excl_tax: float = Field(..., description="Price excluding tax")
    price_incl_tax: float = Field(..., description="Price including tax")
    availability: str = Field(..., description="Availability status")
    num_reviews: int = Field(..., description="Number of reviews")
    image_url: str = Field(..., description="Book cover image URL")
    rating: int = Field(..., description="Star rating (1-5)")
    crawl_timestamp: datetime = Field(..., description="When book was crawled")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "url": "https://books.toscrape.com/catalogue/book_1/index.html",
                "title": "A Light in the Attic",
                "description": "A collection of poems...",
                "category": "Poetry",
                "price_excl_tax": 51.77,
                "price_incl_tax": 51.77,
                "availability": "In stock (22 available)",
                "num_reviews": 0,
                "image_url": "https://books.toscrape.com/media/image.jpg",
                "rating": 3,
                "crawl_timestamp": "2025-11-26T10:00:00Z"
            }
        }

