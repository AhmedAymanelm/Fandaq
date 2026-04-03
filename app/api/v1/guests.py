"""
Guests API — manage guest records per hotel.
"""

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from fastapi import Depends
from app.models.guest import Guest
from app.schemas.guest import (
    GuestResponse, GuestUpdate, GuestListResponse,
)

router = APIRouter(tags=["Guests"])


@router.get(
    "/hotels/{hotel_id}/guests",
    response_model=GuestListResponse,
)
async def list_guests(
    hotel_id: uuid.UUID,
    search: str = Query("", description="Search by name or phone"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all guests for a hotel with optional search."""
    query = select(Guest).where(Guest.hotel_id == hotel_id)

    if search:
        query = query.where(
            (Guest.name.ilike(f"%{search}%")) |
            (Guest.phone.ilike(f"%{search}%")) |
            (Guest.nationality.ilike(f"%{search}%"))
        )

    # Count
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Fetch
    query = query.order_by(Guest.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    guests = result.scalars().all()

    return GuestListResponse(
        guests=[GuestResponse.model_validate(g) for g in guests],
        total=total,
    )


@router.get(
    "/hotels/{hotel_id}/guests/{guest_id}",
    response_model=GuestResponse,
)
async def get_guest(
    hotel_id: uuid.UUID,
    guest_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single guest's details."""
    stmt = select(Guest).where(
        Guest.id == guest_id,
        Guest.hotel_id == hotel_id,
    )
    result = await db.execute(stmt)
    guest = result.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return GuestResponse.model_validate(guest)


@router.put(
    "/hotels/{hotel_id}/guests/{guest_id}",
    response_model=GuestResponse,
)
async def update_guest(
    hotel_id: uuid.UUID,
    guest_id: uuid.UUID,
    data: GuestUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update guest details."""
    stmt = select(Guest).where(
        Guest.id == guest_id,
        Guest.hotel_id == hotel_id,
    )
    result = await db.execute(stmt)
    guest = result.scalar_one_or_none()
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(guest, field, value)

    await db.commit()
    await db.refresh(guest)
    return GuestResponse.model_validate(guest)


@router.delete(
    "/hotels/{hotel_id}/guests/{guest_id}",
    response_model=dict,
)
async def delete_guest(
    hotel_id: uuid.UUID,
    guest_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a guest."""
    stmt = select(Guest).where(
        Guest.id == guest_id,
        Guest.hotel_id == hotel_id,
    )
    result = await db.execute(stmt)
    guest = result.scalar_one_or_none()
    
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
        
    await db.delete(guest)
    await db.commit()
    
    return {"success": True, "message": "تم مسح الضيف بنجاح"}

