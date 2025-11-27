from datetime import datetime
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current server time")
    database: str = Field(..., description="Database status")
    total_books: int = Field(..., description="Total books in database")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-26T10:00:00Z",
                "database": "connected",
                "total_books": 1000
            }
        }

