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


@pytest.mark.asyncio
async def test_rerun_step_increments_preview_version():
    service = PipelineService()
    run = await service.create_run(
        source_type="csv",
        source_locator="packages/db/import/herbs.csv",
    )

    first = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)
    second = await service.rerun_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert first.preview_payload["preview_version"] == 1
    assert second.preview_payload["preview_version"] == 2


@pytest.mark.asyncio
async def test_rollback_to_step_resets_later_steps():
    service = PipelineService()
    run = await service.create_run(
        source_type="csv",
        source_locator="packages/db/import/herbs.csv",
    )

    await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)
    await service.confirm_step(run.id, PipelineStepKey.SOURCE_INGEST)
    await service.preview_step(run.id, PipelineStepKey.SOURCE_PREVIEW)
    await service.confirm_step(run.id, PipelineStepKey.SOURCE_PREVIEW)

    rolled_back = await service.rollback_to_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert rolled_back.current_step == PipelineStepKey.SOURCE_INGEST
    assert rolled_back.steps[PipelineStepKey.SOURCE_INGEST].status == PipelineStepStatus.PENDING
    assert rolled_back.steps[PipelineStepKey.SOURCE_PREVIEW].status == PipelineStepStatus.PENDING


@pytest.mark.asyncio
async def test_mapping_step_returns_shared_model_preview():
    service = PipelineService()
    run = await service.create_run(
        source_type="manual",
        source_locator="陈皮",
    )

    preview = await service.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    assert preview.step == PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL
    assert preview.preview_kind == "graph_mapping"
    assert preview.preview_payload["validation"]["is_valid"] is True
    assert preview.preview_payload["nodes"][0]["type"] == "Herb"
    assert preview.preview_payload["nodes"][0]["name"] == "陈皮"
    assert preview.preview_payload["nodes"][0]["label"] == "药材"


@pytest.mark.asyncio
async def test_mapping_step_with_invalid_candidate_cannot_be_confirmed():
    service = PipelineService()
    run = await service.create_run(
        source_type="manual",
        source_locator="   ",
    )

    preview = await service.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    assert preview.preview_payload["validation"]["is_valid"] is False
    with pytest.raises(ValueError):
        await service.confirm_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)
