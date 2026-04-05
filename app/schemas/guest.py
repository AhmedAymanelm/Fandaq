"""
Guest & Review schemas for API validation.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


# ── Guest Schemas ──

class GuestResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    name: str
    phone: str
    email: str | None = None
    nationality: str | None = None
    id_type: str | None = None
    id_number: str | None = None
    notes: str | None = None
    total_stays: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class GuestUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    nationality: str | None = None
    id_type: str | None = None
    id_number: str | None = None
    notes: str | None = None


class GuestListResponse(BaseModel):
    guests: list[GuestResponse]
    total: int


# ── Review Schemas ──

class ReviewCreate(BaseModel):
    guest_id: uuid.UUID
    reservation_id: uuid.UUID | None = None
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    comment: str | None = None
    category: str = Field(default="general", description="Category: cleanliness, service, maintenance, general")


class ReviewResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    guest_id: uuid.UUID
    reservation_id: uuid.UUID | None = None
    rating: int
    comment: str | None = None
    category: str = "general"
    ai_reply_suggestion: str | None = None
    sentiment: str = "neutral"
    reply_status: str = "pending_approval"
    final_reply_text: str | None = None
    reply_generated_at: datetime | None = None
    reply_approved_at: datetime | None = None
    reply_approved_by_name: str | None = None
    reply_sent_at: datetime | None = None
    reply_sent_channel: str | None = None
    created_at: datetime
    guest_name: str | None = None

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int
    average_rating: float | None = None


class ReviewReplyDecision(BaseModel):
    action: str = Field(..., description="approve, reject, send")
    final_reply_text: str | None = None
