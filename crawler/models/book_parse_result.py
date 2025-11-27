from typing import Optional
from pydantic import BaseModel, Field
from .book import Book

class BookParseResult(BaseModel):
    """Result of parsing a book page."""
    
    success: bool = Field(..., description="Whether parsing succeeded")
    book: Optional[Book] = Field(None, description="Parsed book data")
    error: Optional[str] = Field(None, description="Error message if failed")
    url: str = Field(..., description="URL that was parsed")
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True