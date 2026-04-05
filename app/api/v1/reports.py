"""
Reports API — generate financial reports per hotel.
"""

import uuid
from datetime import date
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from app.database import get_db
from app.api.deps import require_role_for_hotel
from app.models.user import UserRole
from app.schemas.report import ReportResponse, StaffPerformanceResponse
from app.services.report import ReportService

router = APIRouter()


@router.get(
    "/hotels/{hotel_id}/reports/daily",
    response_model=ReportResponse,
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN))],
)
async def daily_report(
    hotel_id: uuid.UUID,
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a daily financial report."""
    return await ReportService.generate_report(
        db, hotel_id, "daily", reference_date=report_date
    )


@router.get(
    "/hotels/{hotel_id}/reports/weekly",
    response_model=ReportResponse,
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN))],
)
async def weekly_report(
    hotel_id: uuid.UUID,
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a weekly financial report."""
    return await ReportService.generate_report(
        db, hotel_id, "weekly", reference_date=report_date
    )


@router.get(
    "/hotels/{hotel_id}/reports/monthly",
    response_model=ReportResponse,
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN))],
)
async def monthly_report(
    hotel_id: uuid.UUID,
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a monthly financial report."""
    return await ReportService.generate_report(
        db, hotel_id, "monthly", reference_date=report_date
    )


@router.get(
    "/hotels/{hotel_id}/reports/staff-performance",
    response_model=StaffPerformanceResponse,
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN, UserRole.SUPERVISOR))],
)
async def staff_performance_report(
    hotel_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Generate staff performance leaderboard for admin/supervisor monitoring."""
    return await ReportService.generate_staff_performance(
        db=db,
        hotel_id=hotel_id,
        period_days=days,
    )


@router.get(
    "/hotels/{hotel_id}/reports/staff-performance/export",
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN, UserRole.SUPERVISOR))],
)
async def export_staff_performance_report(
    hotel_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Export staff performance leaderboard and KPIs as an Excel file."""
    payload = await ReportService.generate_staff_performance(
        db=db,
        hotel_id=hotel_id,
        period_days=days,
    )

    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "ملخص التقييم"
    ws_summary.sheet_view.rightToLeft = True

    summary_headers = ["المؤشر", "القيمة"]
    ws_summary.append(summary_headers)
    for cell in ws_summary[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    summary = payload["summary"]
    summary_rows = [
        ("إجمالي الموظفين", summary["total_staff"]),
        ("الموظفين النشطين", summary["active_staff"]),
        ("إجمالي الشكاوى المحلولة", summary["total_complaints_resolved"]),
        ("إجمالي الحجوزات المعتمدة", summary["total_reservations_approved"]),
        ("متوسط زمن حل الشكاوى (ساعات)", summary["avg_response_hours"]),
        ("متوسط زمن اعتماد الحجز (ساعات)", summary["avg_approval_hours"]),
        ("معدل الرفض (%)", summary["rejection_rate"]),
        ("الفترة", f"{payload['period_start']} -> {payload['period_end']}"),
    ]
    for row in summary_rows:
        ws_summary.append(list(row))

    ws_data = wb.create_sheet("تقييم الموظفين")
    ws_data.sheet_view.rightToLeft = True

    week_headers = []
    if payload["leaderboard"]:
        week_headers = [w["week_start"] for w in payload["leaderboard"][0].get("weekly_trend", [])]

    data_headers = [
        "الترتيب",
        "الاسم",
        "اسم المستخدم",
        "الدور",
        "حل الشكاوى",
        "تأكيد الحجوزات",
        "إجمالي العمليات",
        "متوسط زمن الحل (س)",
        "متوسط زمن الاعتماد (س)",
        "النقاط",
        "آخر نشاط",
    ] + [f"أسبوع {w}" for w in week_headers]

    ws_data.append(data_headers)
    for cell in ws_data[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for row in payload["leaderboard"]:
        week_values = [w["actions"] for w in row.get("weekly_trend", [])]
        ws_data.append([
            row["rank"],
            row["full_name"],
            row["username"],
            row["role"],
            row["complaints_resolved"],
            row["reservations_approved"],
            row["total_actions"],
            row["avg_resolution_hours"],
            row["avg_approval_hours"],
            row["score"],
            row["last_activity_at"] or "-",
            *week_values,
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="staff_performance_{payload["period_end"].replace("-", "")}.xlsx"'
        },
    )
