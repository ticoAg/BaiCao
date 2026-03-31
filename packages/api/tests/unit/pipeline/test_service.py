import pytest

from app.pipeline.materialization import SourceMaterializationService
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
    assert preview.preview_payload["nodes"][0]["type"] == "药材"
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


@pytest.mark.asyncio
async def test_preview_returns_step_specific_payloads():
    service = PipelineService()
    run = await service.create_run(
        source_type="manual",
        source_locator="陈皮。归经：脾经；功效：理气。",
    )

    source_ingest = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)
    source_preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_PREVIEW)
    normalize = await service.preview_step(run.id, PipelineStepKey.NORMALIZE)
    extract = await service.preview_step(run.id, PipelineStepKey.EXTRACT)
    mapping = await service.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)
    human_review = await service.preview_step(run.id, PipelineStepKey.HUMAN_REVIEW)
    export = await service.preview_step(run.id, PipelineStepKey.EXPORT)

    assert source_ingest.preview_kind == "source_descriptor"
    assert source_ingest.preview_payload["adapter"] == "manual"
    assert source_preview.preview_kind == "source_contents"
    assert source_preview.preview_payload["content_preview"]
    assert normalize.preview_kind == "normalized_content"
    assert normalize.preview_payload["normalized_text"]
    assert extract.preview_kind == "extraction_candidates"
    assert extract.preview_payload["candidates"]
    assert mapping.preview_kind == "graph_mapping"
    assert human_review.preview_kind == "review_decision"
    assert human_review.preview_payload["review_items"]
    assert export.preview_kind == "export_plan"
    assert export.preview_payload["export_targets"]


@pytest.mark.asyncio
async def test_extract_step_feeds_map_step_validation():
    service = PipelineService()
    run = await service.create_run(
        source_type="manual",
        source_locator="候选实体：陈皮（药材）",
    )

    await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)
    await service.preview_step(run.id, PipelineStepKey.SOURCE_PREVIEW)
    await service.preview_step(run.id, PipelineStepKey.NORMALIZE)
    extract = await service.preview_step(run.id, PipelineStepKey.EXTRACT)
    mapping = await service.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    assert extract.preview_payload["candidates"][0]["name"] == "陈皮"
    assert mapping.preview_payload["validation"]["is_valid"] is True
    assert mapping.preview_payload["nodes"][0]["name"] == "陈皮"


@pytest.mark.asyncio
async def test_manual_source_builds_text_preview():
    service = PipelineService()
    run = await service.create_run(
        source_type="manual",
        source_locator="陈皮 性温，味辛苦。",
    )

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert preview.preview_kind == "source_descriptor"
    assert preview.preview_payload["adapter"] == "manual"
    assert preview.preview_payload["source_summary"]["kind"] == "text"
    assert preview.preview_payload["source_summary"]["character_count"] > 0


@pytest.mark.asyncio
async def test_jsonl_source_reads_local_file_preview(tmp_path):
    source = tmp_path / "mini.jsonl"
    source.write_text('{"node_name":"陈皮","source":"本草纲目"}\n', encoding="utf-8")
    service = PipelineService()
    run = await service.create_run(source_type="jsonl", source_locator=str(source))

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert preview.preview_kind == "source_descriptor"
    assert preview.preview_payload["adapter"] == "jsonl"
    assert preview.preview_payload["source_summary"]["kind"] == "file"
    assert preview.preview_payload["source_summary"]["sample_lines"][0].startswith('{"node_name":"陈皮"')


@pytest.mark.asyncio
async def test_csv_source_builds_file_preview(tmp_path):
    source = tmp_path / "mini.csv"
    source.write_text("node_name,source\n陈皮,本草纲目\n", encoding="utf-8")
    service = PipelineService()
    run = await service.create_run(source_type="csv", source_locator=str(source))

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert preview.preview_kind == "source_descriptor"
    assert preview.preview_payload["adapter"] == "csv"
    assert preview.preview_payload["source_summary"]["format"] == "csv"
    assert preview.preview_payload["source_summary"]["sample_lines"][0] == "node_name,source"


@pytest.mark.asyncio
async def test_huggingface_source_builds_locator_preview():
    service = PipelineService()
    run = await service.create_run(
        source_type="huggingface",
        source_locator="ZJUFanLab/TCMChat-dataset-600k",
    )

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert preview.preview_kind == "source_descriptor"
    assert preview.preview_payload["adapter"] == "huggingface"
    assert preview.preview_payload["source_summary"]["kind"] == "remote_locator"
    assert preview.preview_payload["source_summary"]["dataset"] == "ZJUFanLab/TCMChat-dataset-600k"


@pytest.mark.asyncio
async def test_source_ingest_preview_returns_materialized_paths(tmp_path, monkeypatch):
    materialization_service = SourceMaterializationService(str(tmp_path))

    def fake_snapshot(repo_id: str, cache_dir):
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "README.md").write_text("# hf repo\n", encoding="utf-8")
        (cache_dir / "data.jsonl").write_text('{"name":"陈皮"}\n', encoding="utf-8")

    monkeypatch.setattr(materialization_service, "_download_huggingface_repo", fake_snapshot)
    service = PipelineService(materialization_service=materialization_service)
    run = await service.create_run(
        source_type="huggingface_repo",
        source_locator="ZJUFanLab/TCMChat-dataset-600k",
        source_payload={
            "source_type": "huggingface_repo",
            "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
        },
    )

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)

    assert preview.preview_payload["run_workdir"]
    assert preview.preview_payload["repo_url"] == "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k"
    assert "/runs/" in preview.preview_payload["run_workdir"]
    assert "/source" not in preview.preview_payload["run_workdir"]
