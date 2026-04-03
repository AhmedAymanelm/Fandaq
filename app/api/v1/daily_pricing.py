"""
Daily Pricing API — manage daily prices for competitors vs our hotel.
"""

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.daily_pricing import DailyPricing
from app.schemas.daily_pricing import (
    DailyPricingCreate,
    DailyPricingUpdate,
    DailyPricingResponse,
    DailyPricingListResponse,
)

router = APIRouter(tags=["Daily Pricing"])


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
    
    pricing = DailyPricing(
        hotel_id=hotel_id,
        competitor_hotel_name=data.competitor_hotel_name,
        date=pricing_date,
        my_price=data.my_price,
        competitor_price=data.competitor_price
    )
    
    try:
        db.add(pricing)
        await db.commit()
        await db.refresh(pricing)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Pricing for {data.competitor_hotel_name} on {pricing_date} already exists."
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
