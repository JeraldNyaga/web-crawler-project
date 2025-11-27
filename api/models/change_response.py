from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

class ChangeResponse(BaseModel):
    """Response model for change records."""
    
    id: str = Field(..., description="Change record ID")
    book_id: str = Field(..., description="Book ID that changed")
    change_type: str = Field(..., description="Type of change")
    old_value: Any = Field(None, description="Old value")
    new_value: Any = Field(None, description="New value")
    changed_at: datetime = Field(..., description="When change was detected")
    book_title: Optional[str] = Field(None, description="Book title")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "book_id": "507f1f77bcf86cd799439011",
                "change_type": "price_change",
                "old_value": 51.77,
                "new_value": 45.99,
                "changed_at": "2025-11-26T10:00:00Z",
                "book_title": "A Light in the Attic"
            }
        }

