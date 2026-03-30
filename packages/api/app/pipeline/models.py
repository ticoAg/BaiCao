from typing import Any
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PipelineRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class PipelineStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PREVIEW_READY = "preview_ready"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    SKIPPED = "skipped"
    FAILED = "failed"


class PipelineStepKey(StrEnum):
    SOURCE_INGEST = "source_ingest"
    SOURCE_PREVIEW = "source_preview"
    NORMALIZE = "normalize"
    EXTRACT = "extract"
    MAP_TO_KNOWLEDGE_MODEL = "map_to_knowledge_model"
    HUMAN_REVIEW = "human_review"
    EXPORT = "export"


PIPELINE_STEP_ORDER = (
    PipelineStepKey.SOURCE_INGEST,
    PipelineStepKey.SOURCE_PREVIEW,
    PipelineStepKey.NORMALIZE,
    PipelineStepKey.EXTRACT,
    PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
    PipelineStepKey.HUMAN_REVIEW,
    PipelineStepKey.EXPORT,
)


class PipelineSourceType(StrEnum):
    HUGGINGFACE_REPO = "huggingface_repo"
    REMOTE_URL = "remote_url"
    LOCAL_UPLOAD = "local_upload"


class PipelineSourceDefinition(BaseModel):
    source_type: PipelineSourceType
    source_input: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True)

    @model_validator(mode="after")
    def validate_source_input(self):
        if self.source_type == PipelineSourceType.HUGGINGFACE_REPO:
            repo_id = str(self.source_input.get("repo_id", "")).strip()
            if not repo_id:
                raise ValueError("repo_id is required for huggingface_repo")
        elif self.source_type == PipelineSourceType.REMOTE_URL:
            url = str(self.source_input.get("url", "")).strip()
            if not url:
                raise ValueError("url is required for remote_url")
        elif self.source_type == PipelineSourceType.LOCAL_UPLOAD:
            upload_token = str(self.source_input.get("upload_token", "")).strip()
            if not upload_token:
                raise ValueError("upload_token is required for local_upload")
        return self

    @property
    def display_locator(self) -> str:
        if self.source_type == PipelineSourceType.HUGGINGFACE_REPO:
            return str(self.source_input.get("repo_id", ""))
        if self.source_type == PipelineSourceType.REMOTE_URL:
            return str(self.source_input.get("url", ""))
        return str(self.source_input.get("upload_token", ""))


class PipelineStepState(BaseModel):
    key: PipelineStepKey
    status: PipelineStepStatus = PipelineStepStatus.PENDING
    summary: str | None = None
    preview_version: int = 0
    preview_kind: str | None = None
    preview_payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=False)


class PipelineRun(BaseModel):
    id: str = Field(default_factory=lambda: f"pipeline-{uuid4()}")
    source_type: str
    source_locator: str
    source_payload: dict[str, Any] = Field(default_factory=dict)
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    current_step: PipelineStepKey = PipelineStepKey.SOURCE_INGEST
    steps: dict[PipelineStepKey, PipelineStepState]

    model_config = ConfigDict(use_enum_values=False)
