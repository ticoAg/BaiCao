"""Herb Pydantic 模型（PostgreSQL 表）"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HerbCreate(BaseModel):
    """创建药材（PostgreSQL）"""
    name: str = Field(description="药材名称")
    latin_name: str | None = Field(default=None, description="拉丁学名")
    category: str = Field(description="药材分类")
    description: str | None = Field(default=None, description="药材说明")

    model_config = ConfigDict(strict=True)


class HerbRead(BaseModel):
    """读取药材"""
    id: UUID = Field(description="药材标识")
    name: str = Field(description="药材名称")
    latin_name: str | None = Field(default=None, description="拉丁学名")
    category: str = Field(description="药材分类")
    description: str | None = Field(default=None, description="药材说明")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")

    model_config = ConfigDict(strict=True)


class HerbUpdate(BaseModel):
    """更新药材"""
    name: str | None = Field(default=None, description="药材名称")
    latin_name: str | None = Field(default=None, description="拉丁学名")
    category: str | None = Field(default=None, description="药材分类")
    description: str | None = Field(default=None, description="药材说明")

    model_config = ConfigDict(strict=True)
