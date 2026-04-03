"""
Guest service — find or create guest records.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest import Guest


class GuestService:

    @staticmethod
    async def find_or_create(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        phone: str,
        name: str = "",
        whatsapp_id: str | None = None,
        nationality: str = "",
        id_number: str = "",
    ) -> Guest:
        """Find existing guest by phone or create a new one."""
        stmt = select(Guest).where(
            Guest.hotel_id == hotel_id,
            Guest.phone == phone,
        )
        result = await db.execute(stmt)
        guest = result.scalar_one_or_none()

        if guest:
            # Update fields if provided
            if name:
                # Always overwrite generic names or empty names
                is_generic = not guest.name or guest.name.strip() in ("", "Guest", "Sir", "WhatsApp User") or guest.name.isdigit() or guest.name == guest.phone
                if is_generic or len(name) > len(guest.name or ""):
                    guest.name = name
            if whatsapp_id and not guest.whatsapp_id:
                guest.whatsapp_id = whatsapp_id
            if nationality and not guest.nationality:
                guest.nationality = nationality
            if id_number and not guest.id_number:
                guest.id_number = id_number
            # Increment stay count for returning guests
            guest.total_stays = (guest.total_stays or 0) + 1
            return guest

        # Create new guest
        guest = Guest(
            hotel_id=hotel_id,
            name=name or "Guest",
            phone=phone,
            whatsapp_id=whatsapp_id,
            nationality=nationality or None,
            id_number=id_number or None,
            total_stays=1,
        )
        db.add(guest)
        await db.flush()
        return guest

    @staticmethod
    async def get_by_whatsapp_id(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        whatsapp_id: str,
    ) -> Guest | None:
        """Find guest by WhatsApp ID."""
        stmt = select(Guest).where(
            Guest.hotel_id == hotel_id,
            Guest.whatsapp_id == whatsapp_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        phone: str,
    ) -> Guest | None:
        """Find guest by phone number."""
        stmt = select(Guest).where(
            Guest.hotel_id == hotel_id,
            Guest.phone == phone,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
