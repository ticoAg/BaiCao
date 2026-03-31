"""Source Pydantic 模型"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import SourceType


class SourceCreate(BaseModel):
    """创建文献来源"""
    name: str = Field(description="来源名称")
    type: SourceType = Field(description="来源类型")
    author: str | None = Field(default=None, description="作者")
    publication_date: str | None = Field(default=None, description="出版日期")
    url: str | None = Field(default=None, description="在线链接")
    isbn: str | None = Field(default=None, description="ISBN 编号")
    pages: str | None = Field(default=None, description="页码范围")
    citation: str = Field(description="引用格式文本")
    description: str | None = Field(default=None, description="来源说明")

    model_config = ConfigDict(strict=True)


class SourceRead(BaseModel):
    """读取文献来源"""
    id: UUID = Field(description="来源标识")
    name: str = Field(description="来源名称")
    type: SourceType = Field(description="来源类型")
    author: str | None = Field(default=None, description="作者")
    publication_date: str | None = Field(default=None, description="出版日期")
    url: str | None = Field(default=None, description="在线链接")
    isbn: str | None = Field(default=None, description="ISBN 编号")
    pages: str | None = Field(default=None, description="页码范围")
    citation: str = Field(description="引用格式文本")
    description: str | None = Field(default=None, description="来源说明")
    created_at: datetime = Field(description="创建时间")

    model_config = ConfigDict(strict=True)
