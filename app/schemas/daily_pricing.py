from datetime import datetime
from datetime import date as pydate
from typing import Optional
import uuid
from pydantic import BaseModel, Field

class DailyPricingBase(BaseModel):
    competitor_hotel_name: str = Field(..., max_length=255)
    my_price: float = Field(..., ge=0)
    competitor_price: float = Field(..., ge=0)

class DailyPricingCreate(DailyPricingBase):
    room_type_id: uuid.UUID
    date: Optional[pydate] = None  # Optional, default to today in DB if not provided

class DailyPricingUpdate(BaseModel):
    competitor_hotel_name: Optional[str] = Field(None, max_length=255)
    my_price: Optional[float] = Field(None, ge=0)
    competitor_price: Optional[float] = Field(None, ge=0)
    room_type_id: Optional[uuid.UUID] = None
    date: Optional[pydate] = None

class DailyPricingResponse(DailyPricingBase):
    id: uuid.UUID
    hotel_id: uuid.UUID
    room_type_id: Optional[uuid.UUID] = None
    date: pydate
    created_at: datetime

    class Config:
        from_attributes = True

class DailyPricingListResponse(BaseModel):
    items: list[DailyPricingResponse]
    total: int
