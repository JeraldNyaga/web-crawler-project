from typing import List
from pydantic import BaseModel, Field
from api.models.change_response import ChangeResponse

class ChangesListResponse(BaseModel):
    """Response model for list of changes."""
    
    changes: List[ChangeResponse] = Field(..., description="List of changes")
    total: int = Field(..., description="Total number of changes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "changes": [
                    {
                        "id": "507f1f77bcf86cd799439012",
                        "change_type": "price_change",
                        "old_value": 51.77,
                        "new_value": 45.99,
                        "changed_at": "2025-11-26T10:00:00Z"
                    }
                ],
                "total": 10
            }
        }

