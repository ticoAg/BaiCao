"""通用 Pydantic 模型"""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PageParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, description="页码，从 1 开始")
    page_size: int = Field(default=20, description="每页条目数")

    model_config = ConfigDict(strict=True)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应"""
    data: T = Field(description="响应数据")
    request_id: str | None = Field(default=None, description="请求标识")
    timestamp: datetime | None = Field(default=None, description="响应时间戳")

    model_config = ConfigDict(strict=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: list[T] = Field(description="当前页条目列表")
    total: int = Field(description="总条目数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条目数")
    has_more: bool = Field(description="是否还有更多数据")

    model_config = ConfigDict(strict=True)
