"""User Pydantic 模型"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.enums import UserRole


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="邮箱")
    password: str = Field(description="密码")
    role: UserRole = Field(default=UserRole.USER, description="用户角色")
    expert_fields: list[str] | None = Field(default=None, description="专家领域列表")

    model_config = ConfigDict(strict=True)


class UserRead(BaseModel):
    """读取用户"""
    id: UUID = Field(description="用户标识")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱")
    role: UserRole = Field(description="用户角色")
    is_active: bool = Field(description="是否启用")
    expert_fields: list[str] = Field(description="专家领域列表")
    verified_at: datetime | None = Field(default=None, description="认证时间")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(strict=True)


class UserUpdate(BaseModel):
    """更新用户"""
    email: EmailStr | None = Field(default=None, description="邮箱")
    role: UserRole | None = Field(default=None, description="用户角色")
    is_active: bool | None = Field(default=None, description="是否启用")
    expert_fields: list[str] | None = Field(default=None, description="专家领域列表")

    model_config = ConfigDict(strict=True)
