"""
Reservation Pydantic schemas.
"""

import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field

from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    room_type: str = Field(..., description="Room type name, e.g. one-bedroom")
    check_in: date
    check_out: date
    guest_name: str = Field("", max_length=255)
    phone: str = Field("", max_length=20)
    notes: str | None = None
    total_price: float | None = None
    status: ReservationStatus | None = None


class ReservationUpdate(BaseModel):
    check_in: date | None = None
    check_out: date | None = None
    notes: str | None = None


class ReservationResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    room_id: uuid.UUID | None
    room_type_id: uuid.UUID
    guest_id: uuid.UUID
    check_in: date
    check_out: date
    status: ReservationStatus
    total_price: float
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReservationDetailResponse(ReservationResponse):
    guest_name: str | None = None
    guest_phone: str | None = None
    room_type_name: str | None = None
    room_number: str | None = None


class ReservationListResponse(BaseModel):
    reservations: list[ReservationDetailResponse]
    total: int


class ReservationActionResponse(BaseModel):
    message: str
    reservation: ReservationResponse
