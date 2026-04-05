"""
API dependencies — database session, authentication, hotel resolution.
"""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.hotel import Hotel
from app.models.user import User, UserRole
from app.services.auth import decode_access_token

# ── Authentication ─────────────────────────────────────

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate JWT token and return the current user."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = uuid.UUID(payload["sub"])
    stmt = select(User).where(User.id == user_id, User.is_active == True)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
        
    return user

def require_role(*allowed_roles: UserRole):
    """Dependency factory to require specific roles."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return role_checker


async def require_hotel_access(
    hotel_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure non-admin users can only access their own hotel's resources."""
    if current_user.role != UserRole.ADMIN and current_user.hotel_id != hotel_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this hotel",
        )
    return current_user


def require_role_for_hotel(*allowed_roles: UserRole):
    """Dependency factory that checks both role and hotel-scoped access."""

    async def role_and_hotel_checker(
        hotel_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        if current_user.role != UserRole.ADMIN and current_user.hotel_id != hotel_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this hotel",
            )
        return current_user

    return role_and_hotel_checker


# ── Database Session ─────────────────────────────────

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Hotel Resolution ─────────────────────────────────

async def get_hotel_by_id(
    hotel_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Hotel:
    """Resolve a hotel by its UUID. Raises 404 if not found."""
    stmt = select(Hotel).where(Hotel.id == hotel_id, Hotel.is_active == True)
    result = await db.execute(stmt)
    hotel = result.scalar_one_or_none()

    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hotel not found: {hotel_id}",
        )
    return hotel


async def get_hotels_by_phone_number_id(
    phone_number_id: str,
    db: AsyncSession,
) -> list[Hotel]:
    """Resolve a list of hotels sharing the same WhatsApp phone number ID."""
    stmt = select(Hotel).where(
        Hotel.whatsapp_phone_number_id == phone_number_id,
        Hotel.is_active == True,
    ).order_by(Hotel.created_at)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_hotels_by_telegram_chat(
    chat_id: str,
    db: AsyncSession,
) -> list[Hotel]:
    """Resolve a list of hotels where the Telegram chat ID matches the owner."""
    stmt = select(Hotel).where(
        Hotel.telegram_owner_chat_id == chat_id,
        Hotel.is_active == True,
    ).order_by(Hotel.created_at)
    result = await db.execute(stmt)
    return list(result.scalars().all())
