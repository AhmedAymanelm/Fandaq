"""
Reports API — generate financial reports per hotel.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.report import ReportResponse
from app.services.report import ReportService

router = APIRouter()


@router.get("/hotels/{hotel_id}/reports/daily", response_model=ReportResponse)
async def daily_report(
    hotel_id: uuid.UUID,
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a daily financial report."""
    return await ReportService.generate_report(
        db, hotel_id, "daily", reference_date=report_date
    )


@router.get("/hotels/{hotel_id}/reports/weekly", response_model=ReportResponse)
async def weekly_report(
    hotel_id: uuid.UUID,
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a weekly financial report."""
    return await ReportService.generate_report(
        db, hotel_id, "weekly", reference_date=report_date
    )


@router.get("/hotels/{hotel_id}/reports/monthly", response_model=ReportResponse)
async def monthly_report(
    hotel_id: uuid.UUID,
    report_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Generate a monthly financial report."""
    return await ReportService.generate_report(
        db, hotel_id, "monthly", reference_date=report_date
    )
