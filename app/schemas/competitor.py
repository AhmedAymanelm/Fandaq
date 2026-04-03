import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CompetitorCreate(BaseModel):
    name: str = Field(..., max_length=255)
    booking_url: str = Field(..., max_length=2048)

class CompetitorResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    name: str
    booking_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class CompetitorListResponse(BaseModel):
    items: list[CompetitorResponse]
    total: int
