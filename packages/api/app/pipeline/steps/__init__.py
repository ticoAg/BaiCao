from app.pipeline.models import PipelineStepKey

from .base import PipelineStepContext, StepHandler
from .export_step import build_export_preview
from .extract import build_extract_preview
from .human_review import build_human_review_preview
from .map_to_knowledge_model import build_map_to_knowledge_model_preview
from .normalize import build_normalize_preview
from .source_ingest import build_source_ingest_preview
from .source_preview import build_source_preview_step


STEP_HANDLERS: dict[PipelineStepKey, StepHandler] = {
    PipelineStepKey.SOURCE_INGEST: build_source_ingest_preview,
    PipelineStepKey.SOURCE_PREVIEW: build_source_preview_step,
    PipelineStepKey.NORMALIZE: build_normalize_preview,
    PipelineStepKey.EXTRACT: build_extract_preview,
    PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL: build_map_to_knowledge_model_preview,
    PipelineStepKey.HUMAN_REVIEW: build_human_review_preview,
    PipelineStepKey.EXPORT: build_export_preview,
}

__all__ = ["PipelineStepContext", "STEP_HANDLERS"]
