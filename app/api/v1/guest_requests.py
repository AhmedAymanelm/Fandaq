"""
Guest Requests API — manage service requests per hotel.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.guest_request import RequestStatus
from app.schemas.guest_request import (
    GuestRequestCreate, GuestRequestResponse,
    GuestRequestStatusUpdate, GuestRequestListResponse,
)
from app.services.guest_request import GuestRequestService

router = APIRouter()


@router.post(
    "/hotels/{hotel_id}/guest-requests",
    response_model=GuestRequestResponse,
    status_code=201,
)
async def create_guest_request(
    hotel_id: uuid.UUID,
    data: GuestRequestCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new guest request."""
    request = await GuestRequestService.create_request(
        db, hotel_id,
        request_type=data.request_type,
        guest_id=data.guest_id,
        details=data.details,
    )
    return request


@router.get(
    "/hotels/{hotel_id}/guest-requests",
    response_model=GuestRequestListResponse,
)
async def list_guest_requests(
    hotel_id: uuid.UUID,
    status: RequestStatus | None = None,
    skip: int = 0,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List guest requests with optional status filter."""
    result = await GuestRequestService.list_requests(
        db, hotel_id, status=status, skip=skip, limit=limit
    )
    return result


@router.patch(
    "/hotels/{hotel_id}/guest-requests/{request_id}",
    response_model=GuestRequestResponse,
)
async def update_request_status(
    hotel_id: uuid.UUID,
    request_id: uuid.UUID,
    data: GuestRequestStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update guest request status."""
    request = await GuestRequestService.update_status(
        db, hotel_id, request_id, data.status
    )
    if not request:
        raise HTTPException(status_code=404, detail="Guest request not found")
    return request
