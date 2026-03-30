import pytest

from app.pipeline.models import (
    PipelineRunStatus,
    PipelineSourceDefinition,
    PipelineStepKey,
    PipelineStepStatus,
)
from app.pipeline.schemas import PipelineStepPreviewResponse


def test_pipeline_has_fixed_step_keys():
    assert PipelineStepKey.SOURCE_INGEST == "source_ingest"
    assert PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL == "map_to_knowledge_model"


def test_pipeline_run_status_has_pending_review():
    assert PipelineRunStatus.PENDING_REVIEW == "pending_review"


def test_pipeline_step_status_has_preview_ready():
    assert PipelineStepStatus.PREVIEW_READY == "preview_ready"


def test_preview_response_has_preview_payload_and_next_step_flag():
    response = PipelineStepPreviewResponse(
        run_id="run-1",
        step=PipelineStepKey.SOURCE_INGEST,
        status=PipelineStepStatus.PREVIEW_READY,
        summary="来源已接入",
        preview_kind="summary",
        preview_payload={"items": 3},
        warnings=[],
        errors=[],
        artifacts=[],
        next_step_ready=False,
    )

    assert response.preview_kind == "summary"
    assert response.preview_payload == {"items": 3}
    assert response.next_step_ready is False


def test_pipeline_source_definition_accepts_huggingface_repo():
    source = PipelineSourceDefinition.model_validate(
        {
            "source_type": "huggingface_repo",
            "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
        }
    )

    assert source.source_type == "huggingface_repo"
    assert source.source_input["repo_id"] == "ZJUFanLab/TCMChat-dataset-600k"


def test_pipeline_source_definition_rejects_missing_repo_id():
    with pytest.raises(Exception) as exc_info:
        PipelineSourceDefinition.model_validate(
            {
                "source_type": "huggingface_repo",
                "source_input": {},
            }
        )

    assert "repo_id" in str(exc_info.value)
