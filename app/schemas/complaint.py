"""
Complaint Pydantic schemas.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.complaint import ComplaintStatus


class ComplaintCreate(BaseModel):
    text: str = Field(..., min_length=1)
    guest_id: uuid.UUID | None = None


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    guest_id: uuid.UUID | None
    guest_name: str | None = None
    guest_phone: str | None = None
    room_number: str | None = None
    text: str
    status: ComplaintStatus
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class ComplaintListResponse(BaseModel):
    complaints: list[ComplaintResponse]
    total: int
