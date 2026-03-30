from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import PipelineStepKey, PipelineStepStatus


class PipelineArtifactReference(BaseModel):
    key: str
    label: str
    uri: str | None = None

    model_config = ConfigDict(use_enum_values=False)


class PipelineStepPreviewResponse(BaseModel):
    run_id: str
    step: PipelineStepKey
    status: PipelineStepStatus
    summary: str
    preview_kind: str
    preview_payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    artifacts: list[PipelineArtifactReference] = Field(default_factory=list)
    next_step_ready: bool = False

    model_config = ConfigDict(use_enum_values=False)


class CreatePipelineRunRequest(BaseModel):
    source_type: str
    source_locator: str
    source_payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)


class PipelineRunResponse(BaseModel):
    id: str
    source_type: str
    source_locator: str
    source_payload: dict[str, Any] = Field(default_factory=dict)
    status: str
    current_step: str
    steps: dict[str, dict[str, Any]]

    model_config = ConfigDict(use_enum_values=False)


class UploadedSourceFileResponse(BaseModel):
    upload_token: str
    filename: str
    stored_path: str
    content_type: str | None = None

    model_config = ConfigDict(use_enum_values=False)
