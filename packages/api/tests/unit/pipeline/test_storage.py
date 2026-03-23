import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.pipeline import PipelineRunModel, PipelineStepArtifactModel
from app.pipeline.models import PipelineStepKey
from app.pipeline.service import PipelineService
from app.pipeline.storage import SQLAlchemyPipelineStorage


async def _make_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            PipelineRunModel.metadata.create_all,
            tables=[PipelineRunModel.__table__, PipelineStepArtifactModel.__table__],
        )
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.mark.asyncio
async def test_sqlalchemy_storage_persists_run_and_steps():
    session_factory = await _make_session_factory()

    async with session_factory() as session:
        storage = SQLAlchemyPipelineStorage(session)
        service = PipelineService(storage=storage)

        created = await service.create_run(
            source_type="huggingface",
            source_locator="ZJUFanLab/TCMChat-dataset-600k",
        )
        await service.preview_step(created.id, PipelineStepKey.SOURCE_INGEST)
        updated = await service.confirm_step(created.id, PipelineStepKey.SOURCE_INGEST)

    async with session_factory() as session:
        storage = SQLAlchemyPipelineStorage(session)
        loaded = await storage.get_run(updated.id)

    assert loaded.id == updated.id
    assert loaded.current_step == PipelineStepKey.SOURCE_PREVIEW
    assert loaded.steps[PipelineStepKey.SOURCE_INGEST].status.value == "confirmed"


@pytest.mark.asyncio
async def test_sqlalchemy_storage_lists_runs_in_reverse_created_order():
    session_factory = await _make_session_factory()

    async with session_factory() as session:
        storage = SQLAlchemyPipelineStorage(session)
        service = PipelineService(storage=storage)
        first = await service.create_run(source_type="csv", source_locator="a.csv")
        second = await service.create_run(source_type="jsonl", source_locator="b.jsonl")

    async with session_factory() as session:
        storage = SQLAlchemyPipelineStorage(session)
        runs = await storage.list_runs()

    assert [run.id for run in runs[:2]] == [second.id, first.id]


@pytest.mark.asyncio
async def test_sqlalchemy_storage_persists_preview_artifact_versions():
    session_factory = await _make_session_factory()

    async with session_factory() as session:
        storage = SQLAlchemyPipelineStorage(session)
        service = PipelineService(storage=storage)
        run = await service.create_run(source_type="manual", source_locator="陈皮")
        await service.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)
        await service.rerun_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    async with session_factory() as session:
        storage = SQLAlchemyPipelineStorage(session)
        latest_preview = await storage.get_latest_preview(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)
        artifacts = await storage.list_preview_artifacts(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    assert latest_preview is not None
    assert latest_preview.preview_payload["preview_version"] == 2
    assert latest_preview.preview_kind == "graph_mapping"
    assert len(artifacts) == 2
    assert artifacts[0].preview_payload["preview_version"] == 2
    assert artifacts[1].preview_payload["preview_version"] == 1
