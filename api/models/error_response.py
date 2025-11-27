from typing import Optional
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid query parameters",
                "details": {"field": "rating", "issue": "must be between 1 and 5"}
            }
        }