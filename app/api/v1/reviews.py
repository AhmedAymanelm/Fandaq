"""
Reviews API — manage guest reviews per hotel.
"""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role_for_hotel
from app.database import get_db
from fastapi import Depends
from app.models.review import Review
from app.models.guest import Guest
from app.models.user import UserRole
from app.schemas.guest import (
    ReviewCreate, ReviewResponse, ReviewListResponse,
)

router = APIRouter(
    tags=["Reviews"],
    dependencies=[Depends(require_role_for_hotel(UserRole.ADMIN, UserRole.SUPERVISOR))],
)


@router.post(
    "/hotels/{hotel_id}/reviews",
    response_model=ReviewResponse,
    status_code=201,
)
async def create_review(
    hotel_id: uuid.UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new review."""
    # Verify guest exists
    guest = await db.get(Guest, data.guest_id)
    if not guest or guest.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Guest not found")

    # Check if already reviewed this reservation
    if data.reservation_id:
        existing = await db.execute(
            select(Review).where(
                Review.guest_id == data.guest_id,
                Review.reservation_id == data.reservation_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Already reviewed")

    review = Review(
        hotel_id=hotel_id,
        guest_id=data.guest_id,
        reservation_id=data.reservation_id,
        rating=data.rating,
        comment=data.comment,
        category=data.category,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    resp = ReviewResponse.model_validate(review)
    resp.guest_name = guest.name
    return resp


@router.get(
    "/hotels/{hotel_id}/reviews",
    response_model=ReviewListResponse,
)
async def list_reviews(
    hotel_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List reviews for a hotel."""
    # Get reviews with guest names
    query = (
        select(Review, Guest.name.label("guest_name"))
        .join(Guest, Review.guest_id == Guest.id)
        .where(Review.hotel_id == hotel_id)
        .order_by(Review.created_at.desc())
    )

    # Count
    count_q = select(func.count()).select_from(
        select(Review.id).where(Review.hotel_id == hotel_id).subquery()
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Average rating
    avg_q = select(func.avg(Review.rating)).where(Review.hotel_id == hotel_id)
    avg_rating = (await db.execute(avg_q)).scalar()

    # Fetch
    result = await db.execute(query.offset(skip).limit(limit))
    rows = result.all()

    reviews = []
    for review, guest_name in rows:
        resp = ReviewResponse.model_validate(review)
        resp.guest_name = guest_name
        reviews.append(resp)

    return ReviewListResponse(
        reviews=reviews,
        total=total,
        average_rating=round(avg_rating, 1) if avg_rating else None,
    )
