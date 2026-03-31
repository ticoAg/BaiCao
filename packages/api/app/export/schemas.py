from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExportRecordResponse(BaseModel):
    id: str = Field(description="导出记录标识")
    run_id: str = Field(description="所属流水线运行标识")
    review_session_id: str = Field(description="关联评审会话标识")
    status: str = Field(description="导出记录状态")
    graph_write_status: str = Field(description="图写入状态")
    snapshot_bucket: str | None = Field(default=None, description="快照对象存储桶")
    snapshot_object_key: str | None = Field(default=None, description="快照对象键")
    snapshot_checksum: str | None = Field(default=None, description="快照校验和")
    snapshot_size: int | None = Field(default=None, description="快照大小（字节）")
    error_message: str | None = Field(default=None, description="导出错误信息")
    retry_count: int = Field(description="导出重试次数")

    model_config = ConfigDict(use_enum_values=False)


class ExportPlanResponse(BaseModel):
    run_id: str = Field(description="所属流水线运行标识")
    review_session_id: str | None = Field(default=None, description="关联评审会话标识")
    export_targets: list[str] = Field(default_factory=list, description="计划导出的目标列表")
    record_count: int = Field(default=0, description="待导出记录数量")
    records: list[dict[str, Any]] = Field(default_factory=list, description="待导出记录预览")
    blocking_issues: list[str] = Field(default_factory=list, description="阻塞导出的检查问题列表")
    latest_execution: ExportRecordResponse | None = Field(default=None, description="最近一次执行记录")

    model_config = ConfigDict(use_enum_values=False)
