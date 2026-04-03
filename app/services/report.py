"""
Report service — generate daily/weekly/monthly financial reports.
"""

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from app.models.room_type import RoomType
from app.services.expense import ExpenseService


class ReportService:

    @staticmethod
    async def generate_report(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        report_type: str,
        reference_date: date | None = None,
    ) -> dict:
        """
        Generate a financial report for a hotel.

        report_type: 'daily', 'weekly', 'monthly'
        reference_date: the date to center the report around (defaults to today)
        """
        ref = reference_date or date.today()

        # Calculate period
        if report_type == "daily":
            period_start = ref
            period_end = ref
        elif report_type == "weekly":
            # Monday to Sunday
            period_start = ref - timedelta(days=ref.weekday())
            period_end = period_start + timedelta(days=6)
        elif report_type == "monthly":
            period_start = ref.replace(day=1)
            # Last day of month
            if ref.month == 12:
                period_end = ref.replace(year=ref.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = ref.replace(month=ref.month + 1, day=1) - timedelta(days=1)
        else:
            period_start = ref
            period_end = ref

        # ── Income ─────────────────────────────────────
        # Sum total_price of confirmed/checked-in/checked-out reservations
        income_stmt = select(func.sum(Reservation.total_price)).where(
            Reservation.hotel_id == hotel_id,
            Reservation.status.in_([
                ReservationStatus.CONFIRMED,
                ReservationStatus.CHECKED_IN,
                ReservationStatus.CHECKED_OUT,
            ]),
            Reservation.check_in <= period_end,
            Reservation.check_out >= period_start,
        )
        income_result = await db.execute(income_stmt)
        total_income = float(income_result.scalar() or 0)

        # Income by room type
        income_by_type_stmt = (
            select(RoomType.name, func.sum(Reservation.total_price))
            .join(RoomType, Reservation.room_type_id == RoomType.id)
            .where(
                Reservation.hotel_id == hotel_id,
                Reservation.status.in_([
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.CHECKED_IN,
                    ReservationStatus.CHECKED_OUT,
                ]),
                Reservation.check_in <= period_end,
                Reservation.check_out >= period_start,
            )
            .group_by(RoomType.name)
        )
        income_by_type_result = await db.execute(income_by_type_stmt)
        income_by_room_type = {
            row[0]: float(row[1]) for row in income_by_type_result.all()
        }

        # ── Reservations count ─────────────────────────
        res_count_stmt = select(func.count(Reservation.id)).where(
            Reservation.hotel_id == hotel_id,
            Reservation.check_in <= period_end,
            Reservation.check_out >= period_start,
            Reservation.status.in_([
                ReservationStatus.CONFIRMED,
                ReservationStatus.CHECKED_IN,
                ReservationStatus.CHECKED_OUT,
            ]),
        )
        res_count_result = await db.execute(res_count_stmt)
        reservations_count = res_count_result.scalar() or 0

        # ── Expenses ───────────────────────────────────
        expenses_by_category = await ExpenseService.get_expenses_by_category(
            db, hotel_id, period_start, period_end
        )
        total_expenses = sum(expenses_by_category.values())

        # ── Occupancy rate ─────────────────────────────
        total_rooms_stmt = select(func.count(Room.id)).where(
            Room.hotel_id == hotel_id
        )
        total_rooms_result = await db.execute(total_rooms_stmt)
        total_rooms = total_rooms_result.scalar() or 1  # Avoid division by zero

        days_in_period = max(1, (period_end - period_start).days + 1)
        total_room_nights = total_rooms * days_in_period
        occupancy_rate = (reservations_count / total_room_nights) * 100 if total_room_nights > 0 else 0

        return {
            "report_type": report_type,
            "period_start": str(period_start),
            "period_end": str(period_end),
            "data": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_profit": total_income - total_expenses,
                "reservations_count": reservations_count,
                "occupancy_rate": round(occupancy_rate, 2),
                "income_by_room_type": income_by_room_type,
                "expenses_by_category": expenses_by_category,
            },
        }
