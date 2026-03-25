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
    id: str = Field(default_factory=lambda: f"export-{uuid4()}")
    run_id: str
    review_session_id: str
    status: ExportRecordStatus = ExportRecordStatus.PENDING
    graph_write_status: GraphWriteStatus = GraphWriteStatus.PENDING
    snapshot_bucket: str | None = None
    snapshot_object_key: str | None = None
    snapshot_checksum: str | None = None
    snapshot_size: int | None = None
    error_message: str | None = None
    retry_count: int = 0
    executed_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=export_now)
    updated_at: datetime = Field(default_factory=export_now)

    model_config = ConfigDict(use_enum_values=False)


class GraphWriteResult(BaseModel):
    nodes_written: int = 0
    edges_written: int = 0

    model_config = ConfigDict(use_enum_values=False)
