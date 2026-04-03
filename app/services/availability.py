"""
Availability service — check room availability per hotel.
"""

import uuid
from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room, RoomStatus
from app.models.room_type import RoomType


class AvailabilityService:

    @staticmethod
    async def check(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        room_type_name: str | None = None,
        check_in: date | None = None,
        check_out: date | None = None,
    ) -> list[dict]:
        """
        Check room availability for a hotel.

        Returns a list of room types with their availability counts.
        If check_in/check_out are provided, accounts for existing reservations.
        """
        # Get room types for this hotel
        stmt = select(RoomType).where(RoomType.hotel_id == hotel_id)
        result = await db.execute(stmt)
        all_types = result.scalars().all()

        room_types = all_types
        if room_type_name and all_types:
            matched = next((rt for rt in all_types if rt.name == room_type_name), None)
            room_types = [matched] if matched else all_types

        availability = []

        for rt in room_types:
            # Count total rooms of this type (excluding maintenance)
            total_stmt = select(func.count(Room.id)).where(
                Room.hotel_id == hotel_id,
                Room.room_type_id == rt.id,
                Room.status != RoomStatus.MAINTENANCE,
            )
            total_result = await db.execute(total_stmt)
            total_rooms = total_result.scalar() or 0

            # Count reserved rooms for the date range
            reserved_count = 0
            if check_in and check_out:
                reserved_stmt = select(func.count(Reservation.id)).where(
                    Reservation.hotel_id == hotel_id,
                    Reservation.room_type_id == rt.id,
                    Reservation.status.in_([
                        ReservationStatus.PENDING,
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.CHECKED_IN,
                    ]),
                    # Overlap condition
                    Reservation.check_in < check_out,
                    Reservation.check_out > check_in,
                )
                reserved_result = await db.execute(reserved_stmt)
                reserved_count = reserved_result.scalar() or 0

            available_count = max(0, total_rooms - reserved_count)

            availability.append({
                "room_type": rt.name,
                "room_type_id": str(rt.id),
                "total_units": total_rooms,
                "available_units": available_count,
                "daily_rate": float(rt.daily_rate),
                "monthly_rate": float(rt.monthly_rate),
                "check_in": str(check_in) if check_in else None,
                "check_out": str(check_out) if check_out else None,
            })

        return availability

    @staticmethod
    async def find_available_room(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        room_type_id: uuid.UUID,
        check_in: date,
        check_out: date,
    ) -> Room | None:
        """Find a specific available room for a date range."""
        # Get IDs of rooms that have overlapping reservations
        reserved_room_ids = select(Reservation.room_id).where(
            Reservation.hotel_id == hotel_id,
            Reservation.room_type_id == room_type_id,
            Reservation.room_id.isnot(None),
            Reservation.status.in_([
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.CHECKED_IN,
            ]),
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        ).subquery()

        # Find a room NOT in the reserved set
        stmt = select(Room).where(
            Room.hotel_id == hotel_id,
            Room.room_type_id == room_type_id,
            Room.status == RoomStatus.AVAILABLE,
            Room.id.notin_(select(reserved_room_ids)),
        ).limit(1)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()
