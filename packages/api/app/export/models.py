from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def export_now() -> datetime:
    return datetime.now(UTC)


class ExportRecordStatus(StrEnum):
    PENDING = "pending"
    SNAPSHOT_WRITTEN = "snapshot_written"
    PARTIAL_FAILED = "partial_failed"
    COMPLETED = "completed"
    FAILED = "failed"


class GraphWriteStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ExportRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"export-{uuid4()}", description="导出记录标识")
    run_id: str = Field(description="所属流水线运行标识")
    review_session_id: str = Field(description="关联评审会话标识")
    status: ExportRecordStatus = Field(default=ExportRecordStatus.PENDING, description="导出记录状态")
    graph_write_status: GraphWriteStatus = Field(default=GraphWriteStatus.PENDING, description="图写入状态")
    snapshot_bucket: str | None = Field(default=None, description="快照对象存储桶")
    snapshot_object_key: str | None = Field(default=None, description="快照对象键")
    snapshot_checksum: str | None = Field(default=None, description="快照校验和")
    snapshot_size: int | None = Field(default=None, description="快照大小（字节）")
    error_message: str | None = Field(default=None, description="导出错误信息")
    retry_count: int = Field(default=0, description="导出重试次数")
    executed_at: datetime | None = Field(default=None, description="开始执行时间")
    completed_at: datetime | None = Field(default=None, description="完成执行时间")
    created_at: datetime = Field(default_factory=export_now, description="创建时间")
    updated_at: datetime = Field(default_factory=export_now, description="更新时间")

    model_config = ConfigDict(use_enum_values=False)


class GraphWriteResult(BaseModel):
    nodes_written: int = Field(default=0, description="写入图数据库的节点数量")
    edges_written: int = Field(default=0, description="写入图数据库的边数量")

    model_config = ConfigDict(use_enum_values=False)
