"""
Rooms API — manage room types and individual rooms per hotel.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.room import Room
from app.models.room_type import RoomType
from app.schemas.room import (
    RoomCreate, RoomResponse, RoomDetailResponse, RoomStatusUpdate,
    RoomTypeCreate, RoomTypeUpdate, RoomTypeResponse,
)

router = APIRouter()


# ── Room Types ───────────────────────────────────────

@router.post(
    "/hotels/{hotel_id}/room-types",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room_type(
    hotel_id: uuid.UUID,
    data: RoomTypeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a room type for a hotel."""
    room_type = RoomType(hotel_id=hotel_id, **data.model_dump())
    db.add(room_type)
    await db.flush()
    await db.refresh(room_type)
    return room_type


@router.get("/hotels/{hotel_id}/room-types", response_model=list[RoomTypeResponse])
async def list_room_types(
    hotel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all room types for a hotel."""
    stmt = select(RoomType).where(RoomType.hotel_id == hotel_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.put(
    "/hotels/{hotel_id}/room-types/{room_type_id}",
    response_model=RoomTypeResponse,
)
async def update_room_type(
    hotel_id: uuid.UUID,
    room_type_id: uuid.UUID,
    data: RoomTypeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a room type."""
    stmt = select(RoomType).where(
        RoomType.id == room_type_id, RoomType.hotel_id == hotel_id
    )
    result = await db.execute(stmt)
    room_type = result.scalar_one_or_none()

    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(room_type, key, value)

    await db.flush()
    await db.refresh(room_type)
    return room_type


from sqlalchemy import delete
from app.models.reservation import Reservation

@router.delete(
    "/hotels/{hotel_id}/room-types/{room_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_room_type(
    hotel_id: uuid.UUID,
    room_type_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a room type and recursively delete associated reservations."""
    stmt = select(RoomType).where(
        RoomType.id == room_type_id, RoomType.hotel_id == hotel_id
    )
    result = await db.execute(stmt)
    room_type = result.scalar_one_or_none()

    if not room_type:
        raise HTTPException(status_code=404, detail="Room type not found")

    try:
        from app.models.room import Room
        # Force cascade delete all reservations linked to this room type
        del_res_stmt = delete(Reservation).where(Reservation.room_type_id == room_type_id)
        await db.execute(del_res_stmt)

        # Force cascade delete all rooms linked to this room type
        del_rooms_stmt = delete(Room).where(Room.room_type_id == room_type_id)
        await db.execute(del_rooms_stmt)

        del_stmt = delete(RoomType).where(RoomType.id == room_type_id)
        await db.execute(del_stmt)
        await db.flush()
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete room type: {str(e)}"
        )

    return None


# ── Rooms ────────────────────────────────────────────

@router.post(
    "/hotels/{hotel_id}/rooms",
    response_model=RoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    hotel_id: uuid.UUID,
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create an individual room."""
    room = Room(hotel_id=hotel_id, **data.model_dump())
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return room


@router.get("/hotels/{hotel_id}/rooms", response_model=list[RoomDetailResponse])
async def list_rooms(
    hotel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all rooms for a hotel with their room type info."""
    stmt = select(Room).where(Room.hotel_id == hotel_id).order_by(Room.room_number)
    result = await db.execute(stmt)
    rooms = result.scalars().all()

    # Eagerly load room types using a single query
    room_type_ids = list({room.room_type_id for room in rooms if room.room_type_id})
    room_types = {}
    if room_type_ids:
        rt_stmt = select(RoomType).where(RoomType.id.in_(room_type_ids))
        rt_result = await db.execute(rt_stmt)
        for rt in rt_result.scalars().all():
            room_types[rt.id] = rt

    response = []
    for room in rooms:
        response.append(RoomDetailResponse(
            id=room.id,
            hotel_id=room.hotel_id,
            room_type_id=room.room_type_id,
            room_number=room.room_number,
            status=room.status,
            created_at=room.created_at,
            room_type=room_types.get(room.room_type_id),
        ))

    return response


@router.patch(
    "/hotels/{hotel_id}/rooms/{room_id}/status",
    response_model=RoomResponse,
)
async def update_room_status(
    hotel_id: uuid.UUID,
    room_id: uuid.UUID,
    data: RoomStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update room status (available, occupied, maintenance)."""
    stmt = select(Room).where(Room.id == room_id, Room.hotel_id == hotel_id)
    result = await db.execute(stmt)
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.status = data.status
    await db.flush()
    await db.refresh(room)
    return room


@router.delete(
    "/hotels/{hotel_id}/rooms/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_room(
    hotel_id: uuid.UUID,
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete an individual room."""
    stmt = select(Room).where(Room.id == room_id, Room.hotel_id == hotel_id)
    result = await db.execute(stmt)
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        del_stmt = delete(Room).where(Room.id == room.id)
        await db.execute(del_stmt)
        await db.flush()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete room: {str(e)}"
        )

    return None

