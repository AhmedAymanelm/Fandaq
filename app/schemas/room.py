"""
Room and RoomType Pydantic schemas.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.room import RoomStatus


# ── Room Type Schemas ────────────────────────────────

class RoomTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="e.g. one-bedroom")
    description: str | None = None
    capacity: int = Field(2, ge=1)
    daily_rate: float = Field(..., gt=0)
    monthly_rate: float = Field(..., gt=0)
    total_units: int = Field(..., ge=1)


class RoomTypeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    capacity: int | None = None
    daily_rate: float | None = None
    monthly_rate: float | None = None
    total_units: int | None = None


class RoomTypeResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    name: str
    description: str | None
    capacity: int
    daily_rate: float
    monthly_rate: float
    total_units: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Room Schemas ─────────────────────────────────────

class RoomCreate(BaseModel):
    room_type_id: uuid.UUID
    room_number: str = Field(..., min_length=1, max_length=20)


class RoomStatusUpdate(BaseModel):
    status: RoomStatus


class RoomResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    room_type_id: uuid.UUID
    room_number: str
    status: RoomStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomDetailResponse(RoomResponse):
    room_type: RoomTypeResponse | None = None

    model_config = {"from_attributes": True}


# ── Availability ─────────────────────────────────────

class AvailabilityQuery(BaseModel):
    room_type: str | None = Field(None, description="Room type name, e.g. one-bedroom")
    check_in: str | None = Field(None, description="Check-in date YYYY-MM-DD")
    check_out: str | None = Field(None, description="Check-out date YYYY-MM-DD")


class AvailabilityResponse(BaseModel):
    room_type: str
    total_units: int
    available_units: int
    daily_rate: float
    monthly_rate: float
    check_in: str | None
    check_out: str | None
