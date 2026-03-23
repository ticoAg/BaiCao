import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .helpers import assert_json_keys, assert_status
from app.main import app
from app.core.database import get_db
from app.models.pipeline import PipelineRunModel


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(PipelineRunModel.metadata.create_all, tables=[PipelineRunModel.__table__])

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()


class TestCreatePipelineRun:
    @pytest.mark.asyncio
    async def test_create_pipeline_run_returns_task_summary(self, client):
        resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "huggingface",
                "source_locator": "ZJUFanLab/TCMChat-dataset-600k",
            },
        )

        assert_status(resp, 201)
        data = resp.json()
        assert_json_keys(data, {"id", "source_type", "source_locator", "status", "current_step", "steps"})
        assert data["source_type"] == "huggingface"
        assert data["current_step"] == "source_ingest"


class TestPipelinePreviewStep:
    @pytest.mark.asyncio
    async def test_preview_step_returns_preview_payload(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "csv",
                "source_locator": "packages/db/import/herbs.csv",
            },
        )
        run_id = create_resp.json()["id"]

        resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/preview")

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(
            data,
            {"run_id", "step", "status", "summary", "preview_kind", "preview_payload", "next_step_ready"},
        )
        assert data["step"] == "source_ingest"
        assert data["status"] == "preview_ready"


class TestPipelineConfirmStep:
    @pytest.mark.asyncio
    async def test_confirm_step_advances_to_next_step(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "csv",
                "source_locator": "packages/db/import/herbs.csv",
            },
        )
        run_id = create_resp.json()["id"]

        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/preview")
        resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/confirm")

        assert_status(resp, 200)
        data = resp.json()
        assert data["current_step"] == "source_preview"


class TestGetPipelineRun:
    @pytest.mark.asyncio
    async def test_get_pipeline_run_returns_persisted_run(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "csv",
                "source_locator": "packages/db/import/herbs.csv",
            },
        )
        run_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/pipeline/runs/{run_id}")

        assert_status(resp, 200)
        data = resp.json()
        assert data["id"] == run_id
        assert data["current_step"] == "source_ingest"
