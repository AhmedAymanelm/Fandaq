"""
Hotel Pydantic schemas.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class HotelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    owner_whatsapp: str = Field(..., min_length=1, max_length=20)
    owner_email: str | None = None
    whatsapp_number: str | None = None
    whatsapp_phone_number_id: str | None = None
    webhook_verify_token: str | None = None
    whatsapp_api_token: str | None = None
    telegram_bot_token: str | None = None
    address: str | None = None
    settings: dict | None = None


class HotelUpdate(BaseModel):
    name: str | None = None
    whatsapp_number: str | None = None
    whatsapp_phone_number_id: str | None = None
    owner_whatsapp: str | None = None
    owner_email: str | None = None
    webhook_verify_token: str | None = None
    whatsapp_api_token: str | None = None
    telegram_bot_token: str | None = None
    address: str | None = None
    is_active: bool | None = None
    settings: dict | None = None


class HotelResponse(BaseModel):
    id: uuid.UUID
    name: str
    whatsapp_number: str | None = None
    whatsapp_phone_number_id: str | None = None
    owner_whatsapp: str
    owner_email: str | None = None
    whatsapp_api_token: str | None = None
    telegram_bot_token: str | None = None
    address: str | None = None
    is_active: bool
    settings: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HotelListResponse(BaseModel):
    hotels: list[HotelResponse]
    total: int
