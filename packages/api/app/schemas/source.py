"""Source Pydantic 模型"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.enums import SourceType


class SourceCreate(BaseModel):
    """创建文献来源"""
    name: str
    type: SourceType
    author: str | None = None
    publication_date: str | None = None
    url: str | None = None
    isbn: str | None = None
    pages: str | None = None
    citation: str
    description: str | None = None

    model_config = ConfigDict(strict=True)


class SourceRead(BaseModel):
    """读取文献来源"""
    id: UUID
    name: str
    type: SourceType
    author: str | None = None
    publication_date: str | None = None
    url: str | None = None
    isbn: str | None = None
    pages: str | None = None
    citation: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(strict=True)
