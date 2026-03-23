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
    preview_payload: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    artifacts: list[PipelineArtifactReference] = Field(default_factory=list)
    next_step_ready: bool = False

    model_config = ConfigDict(use_enum_values=False)


class CreatePipelineRunRequest(BaseModel):
    source_type: str
    source_locator: str

    model_config = ConfigDict(use_enum_values=False)


class PipelineRunResponse(BaseModel):
    id: str
    source_type: str
    source_locator: str
    status: str
    current_step: str
    steps: dict[str, dict[str, object]]

    model_config = ConfigDict(use_enum_values=False)
