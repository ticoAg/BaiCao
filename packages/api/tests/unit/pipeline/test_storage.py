import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.pipeline import PipelineRunModel
from app.pipeline.models import PipelineStepKey
from app.pipeline.service import PipelineService
from app.pipeline.storage import SQLAlchemyPipelineStorage


async def _make_session_factory():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(PipelineRunModel.metadata.create_all, tables=[PipelineRunModel.__table__])
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
