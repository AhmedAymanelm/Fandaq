"""
Report service — generate daily/weekly/monthly financial reports.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint, ComplaintStatus
from app.models.expense import Expense
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from app.models.room_type import RoomType
from app.models.user import User, UserRole
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

    @staticmethod
    async def generate_staff_performance(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        period_days: int = 30,
    ) -> dict:
        """Build a leaderboard for staff performance over the selected period."""
        period_days = max(1, min(period_days, 365))
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=period_days)

        staff_stmt = select(User).where(
            User.hotel_id == hotel_id,
            User.is_active == True,
            User.role.in_([UserRole.EMPLOYEE, UserRole.SUPERVISOR]),
        )
        staff_rows = (await db.execute(staff_stmt)).scalars().all()

        complaint_stats_stmt = (
            select(
                Complaint.resolved_by_user_id,
                func.count(Complaint.id),
                func.avg(
                    func.extract("epoch", Complaint.resolved_at - Complaint.created_at) / 3600.0
                ),
                func.max(Complaint.resolved_at),
            )
            .where(
                Complaint.hotel_id == hotel_id,
                Complaint.status == ComplaintStatus.RESOLVED,
                Complaint.resolved_by_user_id.is_not(None),
                Complaint.resolved_at.is_not(None),
                Complaint.resolved_at >= period_start,
            )
            .group_by(Complaint.resolved_by_user_id)
        )
        complaint_stats = {
            row[0]: {
                "count": int(row[1] or 0),
                "avg_hours": float(row[2] or 0),
                "last_activity": row[3],
            }
            for row in (await db.execute(complaint_stats_stmt)).all()
            if row[0] is not None
        }

        reservation_stats_stmt = (
            select(
                Reservation.approved_by_user_id,
                func.count(Reservation.id),
                func.avg(
                    func.extract("epoch", Reservation.approved_at - Reservation.created_at) / 3600.0
                ),
                func.max(Reservation.approved_at),
            )
            .where(
                Reservation.hotel_id == hotel_id,
                Reservation.approved_by_user_id.is_not(None),
                Reservation.approved_at.is_not(None),
                Reservation.approved_at >= period_start,
            )
            .group_by(Reservation.approved_by_user_id)
        )
        reservation_stats = {
            row[0]: {
                "count": int(row[1] or 0),
                "avg_hours": float(row[2] or 0),
                "last_activity": row[3],
            }
            for row in (await db.execute(reservation_stats_stmt)).all()
            if row[0] is not None
        }

        complaint_events_stmt = select(
            Complaint.resolved_by_user_id,
            Complaint.resolved_at,
        ).where(
            Complaint.hotel_id == hotel_id,
            Complaint.status == ComplaintStatus.RESOLVED,
            Complaint.resolved_by_user_id.is_not(None),
            Complaint.resolved_at.is_not(None),
            Complaint.resolved_at >= period_start,
        )
        complaint_events = (await db.execute(complaint_events_stmt)).all()

        reservation_events_stmt = select(
            Reservation.approved_by_user_id,
            Reservation.approved_at,
        ).where(
            Reservation.hotel_id == hotel_id,
            Reservation.approved_by_user_id.is_not(None),
            Reservation.approved_at.is_not(None),
            Reservation.approved_at >= period_start,
        )
        reservation_events = (await db.execute(reservation_events_stmt)).all()

        week_window = 6
        today = period_end.date()
        current_week_monday = today - timedelta(days=today.weekday())
        week_starts = [current_week_monday - timedelta(days=7 * i) for i in range(week_window - 1, -1, -1)]
        week_key_set = {w.isoformat() for w in week_starts}

        weekly_by_user: dict[uuid.UUID, dict[str, int]] = {}

        def _add_weekly_event(user_id, event_dt):
            if user_id is None or event_dt is None:
                return
            event_date = event_dt.date()
            week_start = event_date - timedelta(days=event_date.weekday())
            week_key = week_start.isoformat()
            if week_key not in week_key_set:
                return
            if user_id not in weekly_by_user:
                weekly_by_user[user_id] = {}
            weekly_by_user[user_id][week_key] = weekly_by_user[user_id].get(week_key, 0) + 1

        for row in complaint_events:
            _add_weekly_event(row[0], row[1])
        for row in reservation_events:
            _add_weekly_event(row[0], row[1])

        decision_counts_stmt = (
            select(
                func.count(Reservation.id).filter(Reservation.status == ReservationStatus.REJECTED),
                func.count(Reservation.id).filter(
                    Reservation.status.in_([
                        ReservationStatus.CONFIRMED,
                        ReservationStatus.CHECKED_IN,
                        ReservationStatus.CHECKED_OUT,
                    ])
                ),
            )
            .where(
                Reservation.hotel_id == hotel_id,
                Reservation.created_at >= period_start,
            )
        )
        rejected_count, accepted_count = (await db.execute(decision_counts_stmt)).one()
        rejected_count = int(rejected_count or 0)
        accepted_count = int(accepted_count or 0)
        total_decisions = rejected_count + accepted_count
        rejection_rate = round((rejected_count / total_decisions) * 100, 2) if total_decisions > 0 else 0.0

        overall_approval_stmt = select(
            func.avg(
                func.extract("epoch", Reservation.approved_at - Reservation.created_at) / 3600.0
            )
        ).where(
            Reservation.hotel_id == hotel_id,
            Reservation.approved_at.is_not(None),
            Reservation.approved_at >= period_start,
        )
        overall_avg_approval_hours = float((await db.execute(overall_approval_stmt)).scalar() or 0.0)

        leaderboard = []
        total_resolved = 0
        weighted_resolution_hours = 0.0

        for idx, user in enumerate(staff_rows):
            c_data = complaint_stats.get(user.id, {})
            r_data = reservation_stats.get(user.id, {})

            complaints_resolved = int(c_data.get("count", 0))
            reservations_approved = int(r_data.get("count", 0))
            avg_resolution_hours = float(c_data.get("avg_hours", 0.0))
            avg_approval_hours = float(r_data.get("avg_hours", 0.0))
            total_actions = complaints_resolved + reservations_approved

            speed_bonus = 0
            if complaints_resolved > 0:
                # Rewards faster resolution with up to +10 bonus points.
                speed_bonus = max(0, 10 - int(avg_resolution_hours // 2))

            score = complaints_resolved * 5 + reservations_approved * 3 + speed_bonus

            last_activity_candidates = [
                c_data.get("last_activity"),
                r_data.get("last_activity"),
            ]
            last_activity_candidates = [d for d in last_activity_candidates if d is not None]
            last_activity = max(last_activity_candidates) if last_activity_candidates else None

            total_resolved += complaints_resolved
            weighted_resolution_hours += avg_resolution_hours * complaints_resolved

            leaderboard.append({
                "user_id": str(user.id),
                "full_name": user.full_name,
                "username": user.username,
                "role": user.role.value,
                "complaints_resolved": complaints_resolved,
                "reservations_approved": reservations_approved,
                "avg_resolution_hours": round(avg_resolution_hours, 2),
                "avg_approval_hours": round(avg_approval_hours, 2),
                "total_actions": total_actions,
                "score": score,
                "rank": idx + 1,
                "last_activity_at": last_activity.isoformat() if last_activity else None,
                "weekly_trend": [
                    {
                        "week_start": w.isoformat(),
                        "actions": weekly_by_user.get(user.id, {}).get(w.isoformat(), 0),
                    }
                    for w in week_starts
                ],
                "_sort_last_activity": last_activity,
            })

        leaderboard.sort(
            key=lambda row: (
                row["score"],
                row["total_actions"],
                row["complaints_resolved"],
                row["_sort_last_activity"] or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )

        for rank, row in enumerate(leaderboard, start=1):
            row["rank"] = rank
            row.pop("_sort_last_activity", None)

        active_staff = sum(1 for row in leaderboard if row["total_actions"] > 0)
        avg_response_hours = (
            round(weighted_resolution_hours / total_resolved, 2) if total_resolved > 0 else 0.0
        )

        return {
            "period_days": period_days,
            "period_start": period_start.date().isoformat(),
            "period_end": period_end.date().isoformat(),
            "summary": {
                "total_staff": len(staff_rows),
                "active_staff": active_staff,
                "total_complaints_resolved": sum(r["complaints_resolved"] for r in leaderboard),
                "total_reservations_approved": sum(r["reservations_approved"] for r in leaderboard),
                "avg_response_hours": avg_response_hours,
                "avg_approval_hours": round(overall_avg_approval_hours, 2),
                "rejection_rate": rejection_rate,
            },
            "leaderboard": leaderboard,
        }
