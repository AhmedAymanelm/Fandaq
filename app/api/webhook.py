"""
WhatsApp & Telegram Webhook — receives and processes incoming messages.

This is the main entry point for all WhatsApp and Telegram communication.
Flow: Webhook → Parser → AI Extractor → Dispatcher → Service → Reply
"""

import logging
import time
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc, select

from app.config import get_settings
from app.database import get_db
from app.models.processed_message import ProcessedMessage
from app.models.room_type import RoomType
from app.ai.extractor import extract_intent
from app.ai.dispatcher import dispatch_intent
from app.services.guest import GuestService
from app.services.whatsapp_session import WhatsAppSessionService
from app.whatsapp.parser import parse_webhook_payload, parse_telegram_update
from app.whatsapp.client import whatsapp_client

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# Configuration
RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMIT_MAX = 15
RATE_LIMIT_WINDOW = 60  # Seconds


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    WhatsApp webhook verification (GET).

    Meta sends a GET request with a challenge to verify the webhook URL.
    We must respond with the challenge if the verify token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning(f"Webhook verification failed. Token: {hub_verify_token}")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    WhatsApp webhook handler (POST).

    Receives incoming WhatsApp messages and processes them through the AI pipeline:
    1. Parse the webhook payload
    2. Identify the hotel (by recipient phone number ID)
    3. Determine if sender is owner or guest
    4. Extract intent via AI
    5. Dispatch to the correct service
    6. Send response back via WhatsApp
    """
    payload = await request.json()
    logger.info(f"Webhook received: {payload}")

    # Parse messages from the WhatsApp payload
    messages = parse_webhook_payload(payload)

    if not messages:
        return {"status": "ok"}

    for msg in messages:
        await _process_message(msg, db, source="whatsapp")

    return {"status": "ok"}


@router.post("/telegram-webhook")
async def receive_telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Telegram Bot webhook handler (POST).

    Receives incoming Telegram messages and processes them through the AI pipeline.
    Same flow as WhatsApp but via Telegram Bot API.
    """
    update = await request.json()
    logger.info(f"Telegram update received: {update}")

    # Parse messages from the Telegram update
    messages = parse_telegram_update(update)

    if not messages:
        return {"status": "ok"}

    for msg in messages:
        await _process_message(msg, db, source="telegram")

    return {"status": "ok"}


@router.post("/telegram-webhook/{hotel_id}")
async def receive_telegram_webhook_per_hotel(
    hotel_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Per-hotel Telegram Bot webhook handler (POST).
    Each hotel registers its own bot webhook to /telegram-webhook/{hotel_id}.
    """
    update = await request.json()
    logger.info(f"Telegram update for hotel {hotel_id}: {update}")

    messages = parse_telegram_update(update)
    if not messages:
        return {"status": "ok"}

    for msg in messages:
        await _process_message(msg, db, source="telegram", forced_hotel_id=hotel_id)

    return {"status": "ok"}


async def _process_message(msg, db: AsyncSession, source: str = "whatsapp", forced_hotel_id: str = None):
    """
    Process a single parsed message (WhatsApp or Telegram).

    Shared pipeline:
    1. Rate limiting
    2. Deduplication
    3. Hotel resolution
    4. Owner/guest detection
    5. AI intent extraction
    6. Action dispatch
    7. Response delivery
    """
    is_telegram = source == "telegram"

    try:
        # 1. Rate Limiting
        now = time.time()
        history = [t for t in RATE_LIMIT_STORE[msg.sender_phone] if now - t < RATE_LIMIT_WINDOW]
        history.append(now)
        RATE_LIMIT_STORE[msg.sender_phone] = history
        
        if len(history) > RATE_LIMIT_MAX:
            logger.warning(f"Rate limit exceeded for {msg.sender_phone}")
            return
            
        # 2. Message Deduplication
        db.add(ProcessedMessage(id=msg.message_id))
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            logger.info(f"Duplicate message ignored: {msg.message_id}")
            return

        # 3. Identify hotels
        if forced_hotel_id:
            # Per-hotel Telegram webhook — resolve hotel directly
            from app.models.hotel import Hotel
            stmt = select(Hotel).where(Hotel.id == uuid.UUID(forced_hotel_id), Hotel.is_active == True)
            result = await db.execute(stmt)
            found_hotel = result.scalar_one_or_none()
            hotels = [found_hotel] if found_hotel else []
        elif is_telegram:
            from app.api.deps import get_hotels_by_telegram_chat
            hotels = await get_hotels_by_telegram_chat(msg.sender_phone, db)
            
            # If no hotel found via telegram mapping, try all active hotels
            if not hotels:
                from app.models.hotel import Hotel
                stmt = select(Hotel).where(Hotel.is_active == True).order_by(Hotel.created_at)
                result = await db.execute(stmt)
                hotels = list(result.scalars().all())
        else:
            from app.api.deps import get_hotels_by_phone_number_id
            hotels = await get_hotels_by_phone_number_id(
                msg.recipient_phone_id, db
            )

        if not hotels:
            source_name = "Telegram" if is_telegram else "WhatsApp"
            logger.warning(
                f"No hotels found for {source_name} sender: {msg.sender_phone}"
            )
            return

        # 4. Determine the active hotel for this user based on their last session
        from app.models.whatsapp_session import WhatsAppSession
        
        hotel_ids = [h.id for h in hotels]
        stmt = select(WhatsAppSession).where(
            WhatsAppSession.whatsapp_user_id == msg.sender_phone,
            WhatsAppSession.hotel_id.in_(hotel_ids)
        ).order_by(desc(WhatsAppSession.last_message_at))
        
        session_result = await db.execute(stmt)
        latest_session = session_result.scalars().first()
        
        if latest_session:
            hotel = next((h for h in hotels if h.id == latest_session.hotel_id), hotels[0])
        else:
            hotel = hotels[0]

        # 5. Mark message as read (WhatsApp only)
        if not is_telegram:
            await whatsapp_client.mark_as_read(
                msg.recipient_phone_id, msg.message_id,
                api_token=hotel.whatsapp_api_token,
            )

        # 6. Determine if sender is owner (for this specific hotel)
        is_owner = msg.sender_phone == hotel.owner_whatsapp
        # For Telegram, also check telegram_owner_chat_id
        if is_telegram and not is_owner:
            is_owner = msg.sender_phone == (hotel.telegram_owner_chat_id or "")

        # 7. Find or create guest
        guest_id = None
        if not is_owner:
            guest = await GuestService.find_or_create(
                db, hotel.id,
                phone=msg.sender_phone,
                name=msg.sender_name or ("Telegram User" if is_telegram else ""),
                whatsapp_id=msg.sender_phone,
            )
            guest_id = guest.id

        # 8. Fetch Session & history
        session = await WhatsAppSessionService.get_or_create_session(
            db, hotel.id, msg.sender_phone
        )
        history = session.context.get("history", []) if session.context else []

        # 8.5 Fetch Hotel Room Types to inject into AI brain
        rt_result = await db.execute(select(RoomType).where(RoomType.hotel_id == hotel.id))
        room_types = [
            {
                "name": rt.name, 
                "capacity": rt.capacity,
                "daily_rate": float(rt.daily_rate),
                "monthly_rate": float(rt.monthly_rate)
            } 
            for rt in rt_result.scalars().all()
        ]

        # 9. Extract intent via AI (same AI brain for WhatsApp & Telegram)
        guest_name_for_ai = None
        guest_nationality_for_ai = None
        guest_id_number_for_ai = None
        
        if not is_owner and guest_id:
            # Only use the name if it's meaningful (not just a phone number or placeholder)
            if guest.name and guest.name != msg.sender_phone and guest.name != "Telegram User":
                guest_name_for_ai = guest.name
            if guest.nationality:
                guest_nationality_for_ai = guest.nationality
            if guest.id_number:
                guest_id_number_for_ai = guest.id_number

        intent_result = await extract_intent(
            msg.text, 
            history=history, 
            hotel_room_types=room_types,
            hotel_name=hotel.name,
            guest_name=guest_name_for_ai,
            guest_nationality=guest_nationality_for_ai,
            guest_id_number=guest_id_number_for_ai,
        )
        
        ai_response = intent_result.get("response")
        intent = intent_result.get("intent")
        data = intent_result.get("data", {})
        
        logger.info(
            f"AI [{msg.source}]: intent={intent}, response={ai_response[:80] if ai_response else 'None'}..."
            f" for hotel={hotel.name}, sender={msg.sender_phone}"
        )

        # 10. Actionable intents — dispatch to service for execution
        ACTIONABLE_INTENTS = {
            "create_reservation", "cancel_reservation", "check_availability",
            "approve_reservation", "reject_reservation", "add_expense",
            "get_report", "guest_request", "complaint", "hotel_selection",
            "submit_review", "update_profile",
        }
        
        response_text = ai_response  # Default: use AI's natural response
        result = {}
        
        if intent in ACTIONABLE_INTENTS:
            result = await dispatch_intent(
                db=db,
                hotel_id=hotel.id,
                intent=intent,
                data=data,
                sender_phone=msg.sender_phone,
                is_owner=is_owner,
                guest_id=guest_id,
            )
            # For actions that produce a result, use the dispatcher's response
            if result.get("response"):
                response_text = result["response"]

        # 11. Handle hotel switching (multi-hotel)
        if result.get("switch_hotel_id"):
            new_hotel_id = uuid.UUID(result["switch_hotel_id"])
            new_session = await WhatsAppSessionService.get_or_create_session(
                db, new_hotel_id, msg.sender_phone
            )
            from datetime import datetime, timezone
            new_session.last_message_at = datetime.now(timezone.utc)
            new_session.context = {"history": []}
            await db.flush()
            hotel = next((h for h in hotels if h.id == new_hotel_id), hotel)
            session = new_session
            logger.info(f"User {msg.sender_phone} switched to hotel {new_hotel_id}")

        # 11b. Clear history on greeting (fresh conversation)
        if intent == "greeting":
            session.context = {"history": []}
            await db.flush()

        # 12. Save conversational memory
        if response_text:
            await WhatsAppSessionService.append_to_history(
                db, session.id, role="user", content=msg.text
            )
            await WhatsAppSessionService.append_to_history(
                db, session.id, role="assistant", content=response_text
            )

        # 13. Send response to sender (WhatsApp or Telegram)
        if response_text:
            tg_token = hotel.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
            if is_telegram:
                await whatsapp_client.send_telegram_message(
                    bot_token=tg_token,
                    chat_id=msg.sender_phone,
                    message=response_text,
                )
            else:
                await whatsapp_client.send_text_message(
                    phone_number_id=hotel.whatsapp_phone_number_id,
                    to=msg.sender_phone,
                    message=response_text,
                    api_token=hotel.whatsapp_api_token,
                )

        # 14. Notify owner if needed (always via WhatsApp, with Telegram fallback)
        if result.get("notify_owner"):
            tg_token = hotel.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
            # Send via WhatsApp
            await whatsapp_client.send_text_message(
                phone_number_id=hotel.whatsapp_phone_number_id,
                to=hotel.owner_whatsapp,
                message=result.get("owner_message", "🔔 إشعار جديد من ضيف."),
                api_token=hotel.whatsapp_api_token,
            )
            # Also send via Telegram if owner has telegram chat ID
            if hotel.telegram_owner_chat_id and tg_token:
                await whatsapp_client.send_telegram_message(
                    bot_token=tg_token,
                    chat_id=hotel.telegram_owner_chat_id,
                    message=result.get("owner_message", "🔔 إشعار جديد من ضيف."),
                )

        # 15. Notify guest if needed (for owner actions like confirm/reject)
        if result.get("notify_guest") and is_owner:
            reservation_id = result.get("reservation_id")
            if reservation_id:
                from app.models.reservation import Reservation
                from app.models.guest import Guest

                stmt = (
                    select(Guest.phone)
                    .join(Reservation, Reservation.guest_id == Guest.id)
                    .where(
                        Reservation.id == reservation_id,
                        Reservation.hotel_id == hotel.id,
                    )
                )
                result_db = await db.execute(stmt)
                guest_phone = result_db.scalar_one_or_none()

                if guest_phone:
                    # Check if this is a Telegram chat ID (numeric) or WhatsApp phone
                    tg_token = hotel.telegram_bot_token or settings.TELEGRAM_BOT_TOKEN
                    guest_message = result.get("guest_message", "")
                    if guest_phone.startswith("tg_") or (guest_phone.isdigit() and len(guest_phone) <= 10):
                        await whatsapp_client.send_telegram_message(
                            bot_token=tg_token,
                            chat_id=guest_phone,
                            message=guest_message,
                        )
                    else:
                        await whatsapp_client.send_text_message(
                            phone_number_id=hotel.whatsapp_phone_number_id,
                            to=guest_phone,
                            message=guest_message,
                            api_token=hotel.whatsapp_api_token,
                        )

        # Commit the transaction
        await db.commit()

    except Exception as e:
        logger.error(f"Error processing message [{msg.source}]: {e}", exc_info=True)
        await db.rollback()

        # Try to send error response
        try:
            tg_token = hotel.telegram_bot_token if 'hotel' in dir() and hotel else settings.TELEGRAM_BOT_TOKEN
            wa_token = hotel.whatsapp_api_token if 'hotel' in dir() and hotel else None
            if is_telegram:
                await whatsapp_client.send_telegram_message(
                    bot_token=tg_token,
                    chat_id=msg.sender_phone,
                    message="عذراً واجهتنا مشكلة بسيطة، ممكن تعيد رسالتك؟ 🙏",
                )
            else:
                await whatsapp_client.send_text_message(
                    phone_number_id=msg.recipient_phone_id,
                    to=msg.sender_phone,
                    message="عذراً واجهتنا مشكلة بسيطة، ممكن تعيد رسالتك؟ 🙏",
                    api_token=wa_token,
                )
        except Exception:
            pass
