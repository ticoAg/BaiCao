import pytest

from app.pipeline.models import PipelineStepKey, PipelineStepStatus
from app.pipeline.service import PipelineService


@pytest.mark.asyncio
async def test_preview_does_not_auto_advance():
    service = PipelineService()
    run = await service.create_run(
        source_type="huggingface",
        source_locator="ZJUFanLab/TCMChat-dataset-600k",
    )

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert preview.step == PipelineStepKey.SOURCE_INGEST
    assert preview.status == PipelineStepStatus.PREVIEW_READY
    loaded = await service.get_run(run.id)
    assert loaded.current_step == PipelineStepKey.SOURCE_INGEST


@pytest.mark.asyncio
async def test_confirm_advances_to_next_step():
    service = PipelineService()
    run = await service.create_run(
        source_type="csv",
        source_locator="packages/db/import/herbs.csv",
    )

    await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)
    updated = await service.confirm_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert updated.current_step == PipelineStepKey.SOURCE_PREVIEW
    assert updated.steps[PipelineStepKey.SOURCE_INGEST].status == PipelineStepStatus.CONFIRMED
