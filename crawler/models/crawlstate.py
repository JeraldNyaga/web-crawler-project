from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CrawlState(BaseModel):
    """Model for tracking crawler state (for resume functionality)."""
    
    state_type: str = Field(default="crawler", description="State identifier")
    last_category: Optional[str] = Field(None, description="Last category crawled")
    last_page: int = Field(default=1, description="Last page number crawled")
    last_book_url: Optional[str] = Field(None, description="Last book URL processed")
    total_books_crawled: int = Field(default=0, description="Total books processed")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="in_progress", description="Crawl status")
    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB storage."""
        return self.model_dump()
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

