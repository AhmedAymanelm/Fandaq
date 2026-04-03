"""
Complaints API — manage guest complaints per hotel.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.complaint import ComplaintStatus
from app.schemas.complaint import (
    ComplaintCreate, ComplaintResponse,
    ComplaintStatusUpdate, ComplaintListResponse,
)
from app.services.complaint import ComplaintService

router = APIRouter()


@router.post(
    "/hotels/{hotel_id}/complaints",
    response_model=ComplaintResponse,
    status_code=201,
)
async def create_complaint(
    hotel_id: uuid.UUID,
    data: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new complaint."""
    complaint = await ComplaintService.create_complaint(
        db, hotel_id, text=data.text, guest_id=data.guest_id
    )
    return complaint


@router.get("/hotels/{hotel_id}/complaints", response_model=ComplaintListResponse)
async def list_complaints(
    hotel_id: uuid.UUID,
    status: ComplaintStatus | None = None,
    skip: int = 0,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List complaints with optional status filter."""
    result = await ComplaintService.list_complaints(
        db, hotel_id, status=status, skip=skip, limit=limit
    )
    return result


from app.models.user import User
from app.api.deps import get_current_user

@router.patch(
    "/hotels/{hotel_id}/complaints/{complaint_id}",
    response_model=ComplaintResponse,
)
async def update_complaint_status(
    hotel_id: uuid.UUID,
    complaint_id: uuid.UUID,
    data: ComplaintStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update complaint status."""
    from app.whatsapp.client import WhatsAppClient
    from app.ai.extractor import client
    from app.config import get_settings
        
    complaint = await ComplaintService.update_status(
        db, hotel_id, complaint_id, data.status
    )
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    # Set transient fields so Pydantic validation passes since we changed the schema
    complaint.guest_name = complaint.guest.name if complaint.guest else None
    complaint.guest_phone = complaint.guest.phone if complaint.guest else None
    complaint.room_number = None # Not fetching room number on patch for simplicity
        
    if data.status == ComplaintStatus.RESOLVED and complaint.guest and complaint.guest.whatsapp_id:
        try:
            employee_name = current_user.full_name
            guest_name_str = complaint.guest.name if complaint.guest and complaint.guest.name else "ضيفنا الكريم"
            
            # Generate AI Apology
            ai_prompt = (
                f"اكتب رسالة واتساب قصيرة وودية ومحترمة من فندق لضيف اسمه '{guest_name_str}'. "
                f"أخبره أنه تم حل شكواه بخصوص: '{complaint.text}'. "
                f"واسم الموظف الذي حل المشكلة هو '{employee_name}'."
            )
            
            settings = get_settings()
            ai_response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": ai_prompt}],
                temperature=0.7,
                max_tokens=200,
            )
            ai_text = ai_response.choices[0].message.content.strip()
            
            if ai_text:
                # We need hotel configuration for whatsapp
                from app.models.hotel import Hotel
                hotel = await db.get(Hotel, hotel_id)
                if hotel:
                    wp_client = WhatsAppClient()
                    guest_phone = complaint.guest.whatsapp_id
                    tg_token = hotel.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
                    
                    if guest_phone and (guest_phone.startswith("tg_") or (guest_phone.isdigit() and len(guest_phone) <= 10)):
                        if tg_token:
                            await wp_client.send_telegram_message(
                                bot_token=tg_token,
                                chat_id=guest_phone,
                                message=ai_text,
                            )
                    elif hotel.whatsapp_phone_number_id:
                        await wp_client.send_text_message(
                            phone_number_id=hotel.whatsapp_phone_number_id,
                            to=guest_phone,
                            message=ai_text,
                            api_token=hotel.whatsapp_api_token
                        )
        except Exception as e:
            # Log error but don't fail the API request
            print(f"Failed to send AI apology message: {e}")
            
    return complaint
