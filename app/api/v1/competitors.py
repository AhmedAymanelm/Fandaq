"""
Competitors API — manage competitor hotels and their booking.com URLs.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role_for_hotel
from app.database import get_db
from app.models.competitor import Competitor
from app.models.user import UserRole
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorResponse,
    CompetitorListResponse,
)

router = APIRouter(
    tags=["Competitors"],
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN, UserRole.SUPERVISOR))],
)


@router.get(
    "/hotels/{hotel_id}/competitors",
    response_model=CompetitorListResponse,
)
async def list_competitors(
    hotel_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Competitor).where(Competitor.hotel_id == hotel_id)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(Competitor.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(query)
    competitors = res.scalars().all()

    return CompetitorListResponse(
        items=[CompetitorResponse.model_validate(c) for c in competitors],
        total=total,
    )


@router.post(
    "/hotels/{hotel_id}/competitors",
    response_model=CompetitorResponse,
    status_code=201,
)
async def create_competitor(
    hotel_id: uuid.UUID,
    data: CompetitorCreate,
    db: AsyncSession = Depends(get_db),
):
    competitor = Competitor(
        hotel_id=hotel_id,
        name=data.name,
        booking_url=str(data.booking_url)
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return CompetitorResponse.model_validate(competitor)


@router.delete(
    "/hotels/{hotel_id}/competitors/{competitor_id}",
    response_model=dict,
)
async def delete_competitor(
    hotel_id: uuid.UUID,
    competitor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Competitor).where(
        Competitor.id == competitor_id,
        Competitor.hotel_id == hotel_id,
    )
    result = await db.execute(stmt)
    competitor = result.scalar_one_or_none()

    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")

    await db.delete(competitor)
    await db.commit()
    return {"success": True, "message": "Competitor deleted"}
