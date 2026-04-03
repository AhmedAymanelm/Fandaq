"""
Reminder Service — sends pre-arrival WhatsApp reminders to guests.
"""

import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import async_session_factory
from app.models.reservation import Reservation, ReservationStatus
from app.models.guest import Guest
from app.models.hotel import Hotel
from app.whatsapp.client import whatsapp_client

logger = logging.getLogger(__name__)


async def send_pre_arrival_reminders():
    """
    Sends a WhatsApp reminder to guests checking in tomorrow.
    Runs daily at 6:00 PM via the scheduler.
    """
    tomorrow = date.today() + timedelta(days=1)
    logger.info(f"🔔 Running pre-arrival reminders for check-in date: {tomorrow}")

    async with async_session_factory() as db:
        # Find all CONFIRMED reservations checking in tomorrow
        stmt = (
            select(Reservation)
            .where(
                Reservation.check_in == tomorrow,
                Reservation.status == ReservationStatus.CONFIRMED,
            )
            .options(
                selectinload(Reservation.guest),
                selectinload(Reservation.hotel),
                selectinload(Reservation.room_type),
            )
        )
        result = await db.execute(stmt)
        reservations = result.scalars().all()

        if not reservations:
            logger.info("No reservations checking in tomorrow. Nothing to remind.")
            return

        sent_count = 0
        for res in reservations:
            guest = res.guest
            hotel = res.hotel
            room_type = res.room_type

            if not guest or not hotel:
                continue

            # Build a friendly reminder message
            guest_name = guest.name if guest.name and guest.name not in ("Sir", "WhatsApp User") else "ضيفنا الكريم"
            
            message = (
                f"مساء الخير {guest_name} 🌙\n\n"
                f"نذكّرك بأن حجزك في *{hotel.name}* غداً إن شاء الله.\n\n"
                f"📋 *تفاصيل حجزك:*\n"
                f"• نوع الغرفة: {room_type.name if room_type else 'غير محدد'}\n"
                f"• تاريخ الدخول: {res.check_in}\n"
                f"• تاريخ الخروج: {res.check_out}\n"
                f"• المبلغ: {res.total_price} ريال\n\n"
                f"⏰ وقت الدخول من الساعة 3:00 عصراً\n\n"
                f"لو تحتاج أي مساعدة أو عندك استفسار، تواصل معنا هنا مباشرة.\n"
                f"بانتظارك! 🏨✨"
            )

            # Send reminder via WhatsApp
            phone = guest.phone
            if not phone:
                continue

            try:
                await whatsapp_client.send_text_message(
                    phone_number_id=hotel.whatsapp_phone_number_id,
                    to=phone,
                    message=message,
                    api_token=hotel.whatsapp_api_token,
                )
                sent_count += 1
                logger.info(f"✅ Reminder sent to {guest_name} ({phone}) for hotel {hotel.name}")
            except Exception as e:
                logger.error(f"❌ Failed to send reminder to {phone}: {e}")

        logger.info(f"🔔 Pre-arrival reminders complete: {sent_count}/{len(reservations)} sent.")
