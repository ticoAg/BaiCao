from app.pipeline.models import PipelineRunStatus, PipelineStepKey, PipelineStepStatus
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
