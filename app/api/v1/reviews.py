"""
Reviews API — manage guest reviews per hotel.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role_for_hotel
from app.database import get_db
from fastapi import Depends
from app.models.review import Review
from app.models.guest import Guest
from app.models.user import User, UserRole
from app.schemas.guest import (
    ReviewCreate, ReviewResponse, ReviewListResponse,
    ReviewReplyDecision,
)


def _review_sentiment_from_rating(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"

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

    from app.ai.extractor import generate_review_reply

    sentiment = _review_sentiment_from_rating(data.rating)
    suggested_reply = await generate_review_reply(data.rating, data.comment, data.category)
    now = datetime.utcnow()
    reply_status = "auto_sent" if sentiment == "positive" else "pending_approval"

    review = Review(
        hotel_id=hotel_id,
        guest_id=data.guest_id,
        reservation_id=data.reservation_id,
        rating=data.rating,
        comment=data.comment,
        category=data.category,
        sentiment=sentiment,
        ai_reply_suggestion=suggested_reply,
        reply_status=reply_status,
        final_reply_text=suggested_reply if sentiment == "positive" else None,
        reply_generated_at=now if suggested_reply else None,
        reply_sent_at=now if sentiment == "positive" else None,
        reply_sent_channel="auto_policy" if sentiment == "positive" else None,
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


@router.patch(
    "/hotels/{hotel_id}/reviews/{review_id}/reply-decision",
    response_model=ReviewResponse,
)
async def review_reply_decision(
    hotel_id: uuid.UUID,
    review_id: uuid.UUID,
    data: ReviewReplyDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Apply moderation workflow to an AI review reply suggestion."""
    review = await db.get(Review, review_id)
    if not review or review.hotel_id != hotel_id:
        raise HTTPException(status_code=404, detail="Review not found")

    action = (data.action or "").strip().lower()
    now = datetime.utcnow()

    if action == "approve":
        if review.sentiment == "positive" and review.reply_status == "auto_sent":
            raise HTTPException(status_code=400, detail="Positive auto-sent reply does not need approval")
        review.reply_status = "approved"
        review.final_reply_text = (data.final_reply_text or review.ai_reply_suggestion or "").strip() or None
        review.reply_approved_at = now
        review.reply_approved_by_user_id = current_user.id
        review.reply_approved_by_name = current_user.full_name
    elif action == "reject":
        review.reply_status = "rejected"
        review.reply_approved_at = now
        review.reply_approved_by_user_id = current_user.id
        review.reply_approved_by_name = current_user.full_name
    elif action == "send":
        if review.sentiment in ("neutral", "negative") and review.reply_status not in ("approved", "sent"):
            raise HTTPException(status_code=400, detail="Neutral/negative reviews must be approved before sending")
        if data.final_reply_text:
            review.final_reply_text = data.final_reply_text.strip() or review.final_reply_text
        if not review.final_reply_text:
            review.final_reply_text = review.ai_reply_suggestion
        review.reply_status = "sent"
        review.reply_sent_at = now
        review.reply_sent_channel = "manual"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Allowed: approve, reject, send")

    await db.commit()
    await db.refresh(review)

    guest = await db.get(Guest, review.guest_id)
    resp = ReviewResponse.model_validate(review)
    resp.guest_name = guest.name if guest else None
    return resp
