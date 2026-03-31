from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import PipelineStepKey, PipelineStepStatus


class PipelineArtifactReference(BaseModel):
    key: str = Field(description="产物键")
    label: str = Field(description="产物标签")
    uri: str | None = Field(default=None, description="产物访问地址")

    model_config = ConfigDict(use_enum_values=False)


class PipelineStepPreviewResponse(BaseModel):
    run_id: str = Field(description="流水线运行标识")
    step: PipelineStepKey = Field(description="当前步骤")
    status: PipelineStepStatus = Field(description="步骤状态")
    summary: str = Field(description="步骤摘要")
    preview_kind: str = Field(description="预览载荷类型")
    preview_payload: dict[str, Any] = Field(default_factory=dict, description="预览载荷内容")
    warnings: list[str] = Field(default_factory=list, description="预览警告列表")
    errors: list[str] = Field(default_factory=list, description="预览错误列表")
    artifacts: list[PipelineArtifactReference] = Field(default_factory=list, description="关联产物列表")
    next_step_ready: bool = Field(default=False, description="下一步是否可执行")

    model_config = ConfigDict(use_enum_values=False)


class CreatePipelineRunRequest(BaseModel):
    source_type: str = Field(description="来源类型")
    source_locator: str = Field(description="来源定位信息")
    source_payload: dict[str, Any] = Field(default_factory=dict, description="来源载荷")

    model_config = ConfigDict(use_enum_values=False)


class PipelineRunResponse(BaseModel):
    id: str = Field(description="流水线运行标识")
    source_type: str = Field(description="来源类型")
    source_locator: str = Field(description="来源定位信息")
    source_payload: dict[str, Any] = Field(default_factory=dict, description="来源载荷")
    status: str = Field(description="流水线运行状态")
    current_step: str = Field(description="当前步骤")
    steps: dict[str, dict[str, Any]] = Field(description="步骤状态映射")

    model_config = ConfigDict(use_enum_values=False)


class UploadedSourceFileResponse(BaseModel):
    upload_token: str = Field(description="上传文件令牌")
    filename: str = Field(description="原始文件名")
    stored_path: str = Field(description="服务端存储路径")
    content_type: str | None = Field(default=None, description="上传文件 MIME 类型")

    model_config = ConfigDict(use_enum_values=False)
