"""User Pydantic 模型"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from ..models.enums import UserRole


class UserCreate(BaseModel):
    """创建用户"""
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER
    expert_fields: list[str] | None = None

    model_config = ConfigDict(strict=True)


class UserRead(BaseModel):
    """读取用户"""
    id: UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    expert_fields: list[str]
    verified_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(strict=True)


class UserUpdate(BaseModel):
    """更新用户"""
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    expert_fields: list[str] | None = None

    model_config = ConfigDict(strict=True)
