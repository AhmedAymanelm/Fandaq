"""
Hotels API — CRUD operations for hotels.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.hotel import Hotel
from app.schemas.hotel import HotelCreate, HotelUpdate, HotelResponse, HotelListResponse

router = APIRouter(prefix="/hotels")


@router.post("", response_model=HotelResponse, status_code=status.HTTP_201_CREATED)
async def create_hotel(
    data: HotelCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new hotel."""
    hotel = Hotel(**data.model_dump())
    db.add(hotel)
    await db.flush()
    await db.refresh(hotel)
    return hotel


@router.get("", response_model=HotelListResponse)
async def list_hotels(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List all hotels."""
    stmt = select(Hotel).order_by(Hotel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    hotels = result.scalars().all()

    count_stmt = select(func.count(Hotel.id))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    return HotelListResponse(hotels=hotels, total=total)


@router.get("/{hotel_id}", response_model=HotelResponse)
async def get_hotel(
    hotel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get hotel by ID."""
    stmt = select(Hotel).where(Hotel.id == hotel_id)
    result = await db.execute(stmt)
    hotel = result.scalar_one_or_none()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel


@router.put("/{hotel_id}", response_model=HotelResponse)
async def update_hotel(
    hotel_id: uuid.UUID,
    data: HotelUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update hotel details."""
    stmt = select(Hotel).where(Hotel.id == hotel_id)
    result = await db.execute(stmt)
    hotel = result.scalar_one_or_none()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(hotel, key, value)

    await db.flush()
    await db.refresh(hotel)
    return hotel


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotel(
    hotel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a hotel and all its related data."""
    stmt = select(Hotel).where(Hotel.id == hotel_id)
    result = await db.execute(stmt)
    hotel = result.scalar_one_or_none()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    await db.delete(hotel)
    await db.flush()
