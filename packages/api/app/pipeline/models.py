from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


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


class PipelineStepState(BaseModel):
    key: PipelineStepKey
    status: PipelineStepStatus = PipelineStepStatus.PENDING
    summary: str | None = None
    preview_version: int = 0
    preview_kind: str | None = None
    preview_payload: dict[str, object] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=False)


class PipelineRun(BaseModel):
    id: str = Field(default_factory=lambda: f"pipeline-{uuid4()}")
    source_type: str
    source_locator: str
    status: PipelineRunStatus = PipelineRunStatus.PENDING
    current_step: PipelineStepKey = PipelineStepKey.SOURCE_INGEST
    steps: dict[PipelineStepKey, PipelineStepState]

    model_config = ConfigDict(use_enum_values=False)
