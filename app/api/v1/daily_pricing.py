"""
Daily Pricing API — manage daily prices for competitors vs our hotel.
"""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import require_role_for_hotel
from app.database import get_db
from app.models.daily_pricing import DailyPricing
from app.models.room_type import RoomType
from app.models.user import UserRole
from app.schemas.daily_pricing import (
    DailyPricingCreate,
    DailyPricingUpdate,
    DailyPricingResponse,
    DailyPricingListResponse,
)

router = APIRouter(
    tags=["Daily Pricing"],
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN, UserRole.SUPERVISOR))],
)


async def _validate_room_type_belongs_to_hotel(
    db: AsyncSession,
    hotel_id: uuid.UUID,
    room_type_id: uuid.UUID,
) -> None:
    room_type = await db.get(RoomType, room_type_id)
    if not room_type or room_type.hotel_id != hotel_id:
        raise HTTPException(status_code=400, detail="Invalid room_type_id for this hotel")


@router.get(
    "/hotels/{hotel_id}/daily-pricing",
    response_model=DailyPricingListResponse,
)
async def list_daily_pricing(
    hotel_id: uuid.UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List daily pricing with optional date filters."""
    query = select(DailyPricing).where(DailyPricing.hotel_id == hotel_id)

    if from_date:
        query = query.where(DailyPricing.date >= from_date)
    if to_date:
        query = query.where(DailyPricing.date <= to_date)

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    query = query.order_by(DailyPricing.date.desc(), DailyPricing.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    prices = result.scalars().all()

    return DailyPricingListResponse(
        items=[DailyPricingResponse.model_validate(p) for p in prices],
        total=total,
    )


@router.post(
    "/hotels/{hotel_id}/daily-pricing",
    response_model=DailyPricingResponse,
    status_code=201,
)
async def create_daily_pricing(
    hotel_id: uuid.UUID,
    data: DailyPricingCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a daily pricing entry."""
    pricing_date = data.date if data.date else date.today()
    await _validate_room_type_belongs_to_hotel(db, hotel_id, data.room_type_id)
    
    pricing = DailyPricing(
        hotel_id=hotel_id,
        competitor_hotel_name=data.competitor_hotel_name,
        date=pricing_date,
        my_price=data.my_price,
        competitor_price=data.competitor_price,
        room_type_id=data.room_type_id,
    )
    
    try:
        db.add(pricing)
        await db.commit()
        await db.refresh(pricing)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Pricing for {data.competitor_hotel_name} on {pricing_date} and selected room type already exists."
        )

    return DailyPricingResponse.model_validate(pricing)


@router.put(
    "/hotels/{hotel_id}/daily-pricing/{pricing_id}",
    response_model=DailyPricingResponse,
)
async def update_daily_pricing(
    hotel_id: uuid.UUID,
    pricing_id: uuid.UUID,
    data: DailyPricingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a daily pricing entry."""
    stmt = select(DailyPricing).where(
        DailyPricing.id == pricing_id,
        DailyPricing.hotel_id == hotel_id,
    )
    result = await db.execute(stmt)
    pricing = result.scalar_one_or_none()
    
    if not pricing:
        raise HTTPException(status_code=404, detail="Daily pricing entry not found")

    update_data = data.model_dump(exclude_unset=True)
    if "room_type_id" in update_data and update_data["room_type_id"] is not None:
        await _validate_room_type_belongs_to_hotel(db, hotel_id, update_data["room_type_id"])

    for field, value in update_data.items():
        setattr(pricing, field, value)

    try:
        await db.commit()
        await db.refresh(pricing)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Update causes duplicate entry")

    return DailyPricingResponse.model_validate(pricing)


@router.delete(
    "/hotels/{hotel_id}/daily-pricing/{pricing_id}",
    response_model=dict,
)
async def delete_daily_pricing(
    hotel_id: uuid.UUID,
    pricing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a daily pricing entry."""
    stmt = select(DailyPricing).where(
        DailyPricing.id == pricing_id,
        DailyPricing.hotel_id == hotel_id,
    )
    result = await db.execute(stmt)
    pricing = result.scalar_one_or_none()
    
    if not pricing:
        raise HTTPException(status_code=404, detail="Daily pricing entry not found")

    await db.delete(pricing)
    await db.commit()

    return {"success": True, "message": "Pricing entry deleted"}


@router.get(
    "/hotels/{hotel_id}/daily-pricing/export",
    tags=["Reports"],
)
async def export_daily_pricing(
    hotel_id: uuid.UUID,
    report_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
):
    """Export daily pricing for a specific date as CSV."""
    import io
    from fastapi.responses import Response
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment

    stmt = select(DailyPricing).where(
        DailyPricing.hotel_id == hotel_id,
        DailyPricing.date == report_date
    ).order_by(DailyPricing.my_price.asc())

    result = await db.execute(stmt)
    prices = result.scalars().all()

    wb = Workbook()
    ws = wb.active
    ws.title = "التسعير اليومي"
    ws.sheet_view.rightToLeft = True

    headers = ["اسم الفندق المنافس", "تاريخ التسعيرة", "سعر الفندق المنافس", "سعر فندقنا", "الفرق"]
    ws.append(headers)
    
    # Style headers
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for p in prices:
        diff = float(p.my_price - p.competitor_price)
        if diff > 0:
            diff_text = f"أغلى بـ {diff}"
        elif diff < 0:
            diff_text = f"أرخص بـ {abs(diff)}"
        else:
            diff_text = "نفس السعر"
            
        ws.append([
            p.competitor_hotel_name,
            p.date.strftime("%Y-%m-%d"),
            float(p.competitor_price),
            float(p.my_price),
            diff_text
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="daily_pricing_{report_date.strftime("%Y%m%d")}.xlsx"'}
    )


@router.post(
    "/hotels/{hotel_id}/daily-pricing/send-report",
    response_model=dict,
)
async def send_daily_pricing_report(
    hotel_id: uuid.UUID,
    report_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
):
    """Manually send combined report to admin/supervisor emails (pricing two days + staff performance)."""
    from app.models.hotel import Hotel
    from app.services.report_delivery import send_combined_pricing_staff_report

    hotel = await db.get(Hotel, hotel_id)
    if not hotel:
        raise HTTPException(404, "Hotel not found")

    result = await send_combined_pricing_staff_report(
        db=db,
        hotel=hotel,
        report_date=report_date,
        staff_days=30,
    )
    if not result.get("success"):
        raise HTTPException(400, result.get("message", "فشل إرسال التقرير"))

    return {
        "success": True,
        "message": "تم إرسال التقرير الموحد بنجاح للمدير/المشرف",
        "recipients": result.get("recipients", []),
        "delivery_channel": "email",
    }
