"""
GuestRequest Pydantic schemas.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.guest_request import RequestStatus


class GuestRequestCreate(BaseModel):
    request_type: str = Field(..., min_length=1, max_length=100)
    details: str | None = None
    guest_id: uuid.UUID | None = None


class GuestRequestStatusUpdate(BaseModel):
    status: RequestStatus


class GuestRequestResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    guest_id: uuid.UUID | None
    request_type: str
    details: str | None
    status: RequestStatus
    acknowledged_at: datetime | None = None
    first_response_by_name: str | None = None
    created_at: datetime
    completed_at: datetime | None
    completed_by_name: str | None = None

    model_config = {"from_attributes": True}


class GuestRequestListResponse(BaseModel):
    requests: list[GuestRequestResponse]
    total: int
