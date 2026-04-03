"""
Auth service — password hashing, JWT tokens, and user management.
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Password Hashing ────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ── JWT Tokens ───────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


# ── User Service ─────────────────────────────────────

class AuthService:

    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> User | None:
        """Authenticate a user by username and password."""
        stmt = select(User).where(User.username == username, User.is_active == True)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user and verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
        """Get a user by their ID."""
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        password: str,
        full_name: str,
        role: str,
        hotel_id: uuid.UUID,
    ) -> User:
        """Create a new user."""
        user = User(
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole(role),
            hotel_id=hotel_id,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def list_users(db: AsyncSession, hotel_id: uuid.UUID | None = None) -> list[User]:
        """List all users, optionally filtered by hotel."""
        stmt = select(User).order_by(User.created_at.desc())
        if hotel_id:
            stmt = stmt.where(User.hotel_id == hotel_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Hard-delete a user."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return False
            
        await db.delete(user)
        await db.commit()
        return True

    @staticmethod
    async def toggle_user_status(db: AsyncSession, user_id: uuid.UUID) -> bool | None:
        """Toggle user is_active status."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
            
        user.is_active = not user.is_active
        await db.commit()
        return user.is_active

    @staticmethod
    async def change_password(
        db: AsyncSession, user_id: uuid.UUID,
        current_password: str, new_password: str,
    ) -> bool:
        """Change a user's password after verifying the current one."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return False

        if not verify_password(current_password, user.password_hash):
            raise ValueError("كلمة المرور الحالية غير صحيحة")

        user.password_hash = hash_password(new_password)
        await db.commit()
        logger.info(f"Password changed for user {user.username}")
        return True

    @staticmethod
    async def update_profile(
        db: AsyncSession, user_id: uuid.UUID, full_name: str,
    ) -> User | None:
        """Update user profile info."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None

        user.full_name = full_name
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def ensure_default_admin(db: AsyncSession) -> None:
        """Create default admin user if no admin exists."""
        stmt = select(User).where(User.role == UserRole.ADMIN)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return  # Admin already exists

        # Get first hotel
        from app.models.hotel import Hotel
        hotel_result = await db.execute(select(Hotel).limit(1))
        hotel = hotel_result.scalar_one_or_none()
        if not hotel:
            logger.warning("No hotels found, skipping default admin creation")
            return

        admin = User(
            username="admin",
            password_hash=hash_password("rosegate2024"),
            full_name="المدير العام",
            role=UserRole.ADMIN,
            hotel_id=hotel.id,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        logger.info(f"Default admin user created for hotel: {hotel.name}")
