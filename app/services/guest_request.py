"""
Guest request service — handle service requests.
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_request import GuestRequest, RequestStatus
from app.models.user import User


class GuestRequestService:

    @staticmethod
    async def create_request(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        request_type: str,
        guest_id: uuid.UUID | None = None,
        details: str | None = None,
    ) -> GuestRequest:
        """Create a new guest request."""
        request = GuestRequest(
            hotel_id=hotel_id,
            guest_id=guest_id,
            request_type=request_type.strip().lower(),
            details=details,
            status=RequestStatus.OPEN,
        )
        db.add(request)
        await db.flush()
        return request

    @staticmethod
    async def update_status(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        request_id: uuid.UUID,
        status: RequestStatus,
        actor_user: User | None = None,
    ) -> GuestRequest | None:
        """Update the status of a guest request."""
        stmt = select(GuestRequest).where(
            GuestRequest.id == request_id,
            GuestRequest.hotel_id == hotel_id,
        )
        result = await db.execute(stmt)
        request = result.scalar_one_or_none()

        if not request:
            return None

        previous_status = request.status
        request.status = status

        if status == RequestStatus.IN_PROGRESS and previous_status == RequestStatus.OPEN:
            if not request.acknowledged_at:
                request.acknowledged_at = datetime.utcnow()
            if actor_user and not request.first_response_by_user_id:
                request.first_response_by_user_id = actor_user.id
                request.first_response_by_name = actor_user.full_name

        if status == RequestStatus.COMPLETED:
            if not request.acknowledged_at:
                request.acknowledged_at = datetime.utcnow()
            if actor_user and not request.first_response_by_user_id:
                request.first_response_by_user_id = actor_user.id
                request.first_response_by_name = actor_user.full_name
            request.completed_at = datetime.utcnow()
            if actor_user:
                request.completed_by_user_id = actor_user.id
                request.completed_by_name = actor_user.full_name
        elif status == RequestStatus.OPEN:
            request.acknowledged_at = None
            request.first_response_by_user_id = None
            request.first_response_by_name = None
            request.completed_by_user_id = None
            request.completed_by_name = None
            request.completed_at = None

        await db.flush()
        return request

    @staticmethod
    async def list_requests(
        db: AsyncSession,
        hotel_id: uuid.UUID,
        status: RequestStatus | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> dict:
        """List guest requests with optional status filter."""
        stmt = select(GuestRequest).where(GuestRequest.hotel_id == hotel_id)
        count_stmt = select(func.count(GuestRequest.id)).where(
            GuestRequest.hotel_id == hotel_id
        )

        if status:
            stmt = stmt.where(GuestRequest.status == status)
            count_stmt = count_stmt.where(GuestRequest.status == status)

        stmt = stmt.order_by(GuestRequest.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        requests = result.scalars().all()

        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        return {"requests": requests, "total": total}
