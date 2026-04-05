"""
Auth API — login, register, user management.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    UserLogin, UserCreate, UserResponse,
    TokenResponse, UserListResponse,
    ChangePasswordRequest, UpdateProfileRequest, UpdateUserEmailRequest,
)
from app.services.auth import AuthService, create_access_token
from app.api.deps import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate and get JWT token."""
    user = await AuthService.authenticate(db, data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user info."""
    return UserResponse.model_validate(current_user)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Create a new user (admin only - enforced via frontend for now)."""
    from sqlalchemy import select
    from app.models.user import User

    # Check username uniqueness
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="اسم المستخدم مستخدم بالفعل",
        )

    normalized_email = data.email.strip().lower() if data.email else None
    if data.role in (UserRole.ADMIN.value, UserRole.SUPERVISOR.value) and not normalized_email:
        raise HTTPException(
            status_code=400,
            detail="إيميل المدير/المشرف مطلوب لإرسال التقارير",
        )

    if normalized_email:
        email_exists = await db.execute(select(User).where(User.email == normalized_email))
        if email_exists.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="الإيميل مستخدم بالفعل",
            )

    user = await AuthService.create_user(
        db,
        username=data.username,
        email=normalized_email,
        password=data.password,
        full_name=data.full_name,
        role=data.role,
        hotel_id=data.hotel_id,
    )
    return UserResponse.model_validate(user)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    hotel_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """List all users."""
    users = await AuthService.list_users(db, hotel_id)
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=len(users),
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Delete (deactivate) a user."""
    success = await AuthService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"message": "تم حذف المستخدم بنجاح"}

@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Toggle user active status."""
    new_status = await AuthService.toggle_user_status(db, user_id)
    if new_status is None:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"is_active": new_status, "message": "تم تحديث حالة المستخدم"}


@router.patch("/users/{user_id}/email", response_model=UserResponse)
async def update_user_email(
    user_id: uuid.UUID,
    data: UpdateUserEmailRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    """Update user's email used for sending reports."""
    try:
        updated = await AuthService.update_user_email(db, user_id, data.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    return UserResponse.model_validate(updated)

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password (requires authentication)."""
    try:
        success = await AuthService.change_password(
            db, current_user.id, data.current_password, data.new_password
        )
        if not success:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "تم تغيير كلمة المرور بنجاح"}


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile (requires authentication)."""
    user = await AuthService.update_profile(db, current_user.id, data.full_name)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return UserResponse.model_validate(user)

