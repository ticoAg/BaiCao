from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExportRecordResponse(BaseModel):
    id: str
    run_id: str
    review_session_id: str
    status: str
    graph_write_status: str
    snapshot_bucket: str | None = None
    snapshot_object_key: str | None = None
    snapshot_checksum: str | None = None
    snapshot_size: int | None = None
    error_message: str | None = None
    retry_count: int

    model_config = ConfigDict(use_enum_values=False)


class ExportPlanResponse(BaseModel):
    run_id: str
    review_session_id: str | None = None
    export_targets: list[str] = Field(default_factory=list)
    record_count: int = 0
    records: list[dict[str, Any]] = Field(default_factory=list)
    blocking_issues: list[str] = Field(default_factory=list)
    latest_execution: ExportRecordResponse | None = None

    model_config = ConfigDict(use_enum_values=False)
