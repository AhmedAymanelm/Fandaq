"""
User schemas for authentication and RBAC.
"""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: str = Field(default="employee", description="admin, supervisor, employee")
    hotel_id: uuid.UUID


class UserResponse(BaseModel):
    id: uuid.UUID
    hotel_id: uuid.UUID
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, description="كلمة المرور الجديدة (6 أحرف على الأقل)")


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
