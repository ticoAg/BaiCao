"""Herb Pydantic 模型（PostgreSQL 表）"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class HerbCreate(BaseModel):
    """创建药材（PostgreSQL）"""
    name: str
    latin_name: str | None = None
    category: str
    description: str | None = None

    model_config = ConfigDict(strict=True)


class HerbRead(BaseModel):
    """读取药材"""
    id: UUID
    name: str
    latin_name: str | None = None
    category: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(strict=True)


class HerbUpdate(BaseModel):
    """更新药材"""
    name: str | None = None
    latin_name: str | None = None
    category: str | None = None
    description: str | None = None

    model_config = ConfigDict(strict=True)
