"""通用 Pydantic 模型"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PageParams(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 20

    model_config = ConfigDict(strict=True)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    data: T
    request_id: str | None = None
    timestamp: datetime | None = None

    model_config = ConfigDict(strict=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool

    model_config = ConfigDict(strict=True)
