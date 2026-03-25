import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .helpers import assert_json_keys, assert_status
from app.main import app
from app.core.database import get_db
from app.models.pipeline import PipelineRunModel, PipelineStepArtifactModel


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            PipelineRunModel.metadata.create_all,
            tables=[PipelineRunModel.__table__, PipelineStepArtifactModel.__table__],
        )

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
        assert data["preview_kind"] == "source_descriptor"
        assert data["preview_payload"]["adapter"] == "csv"
        assert data["preview_payload"]["source_summary"]["format"] == "csv"

    @pytest.mark.asyncio
    async def test_preview_routes_return_step_specific_payloads(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "manual",
                "source_locator": "候选实体：陈皮（药材）",
            },
        )
        run_id = create_resp.json()["id"]

        source_preview = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_preview/preview")
        normalize = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/normalize/preview")
        extract = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/extract/preview")
        mapping = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")

        assert_status(source_preview, 200)
        assert_status(normalize, 200)
        assert_status(extract, 200)
        assert_status(mapping, 200)
        assert source_preview.json()["preview_kind"] == "source_contents"
        assert normalize.json()["preview_kind"] == "normalized_content"
        assert extract.json()["preview_kind"] == "extraction_candidates"
        assert extract.json()["preview_payload"]["candidates"][0]["name"] == "陈皮"
        assert mapping.json()["preview_payload"]["nodes"][0]["name"] == "陈皮"

    @pytest.mark.asyncio
    async def test_get_latest_preview_returns_persisted_snapshot(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "manual",
                "source_locator": "陈皮",
            },
        )
        run_id = create_resp.json()["id"]

        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")
        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/rerun")
        resp = await client.get(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")

        assert_status(resp, 200)
        data = resp.json()
        assert data["preview_kind"] == "graph_mapping"
        assert data["preview_payload"]["preview_version"] == 2

    @pytest.mark.asyncio
    async def test_list_preview_artifacts_returns_version_history(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={
                "source_type": "manual",
                "source_locator": "陈皮",
            },
        )
        run_id = create_resp.json()["id"]

        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")
        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/rerun")
        resp = await client.get(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/artifacts")

        assert_status(resp, 200)
        data = resp.json()
        assert len(data) == 2
        assert data[0]["preview_payload"]["preview_version"] == 2
        assert data[1]["preview_payload"]["preview_version"] == 1


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


class TestListPipelineRuns:
    @pytest.mark.asyncio
    async def test_list_pipeline_runs_returns_recent_runs(self, client):
        await client.post(
            "/api/v1/pipeline/runs",
            json={"source_type": "csv", "source_locator": "packages/db/import/herbs.csv"},
        )
        await client.post(
            "/api/v1/pipeline/runs",
            json={"source_type": "jsonl", "source_locator": "packages/db/import/herbs.jsonl"},
        )

        resp = await client.get("/api/v1/pipeline/runs")

        assert_status(resp, 200)
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert data[0]["source_locator"] == "packages/db/import/herbs.jsonl"


class TestPipelineRerunAndRollback:
    @pytest.mark.asyncio
    async def test_rerun_step_returns_new_preview_version(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={"source_type": "csv", "source_locator": "packages/db/import/herbs.csv"},
        )
        run_id = create_resp.json()["id"]

        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/preview")
        resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/rerun")

        assert_status(resp, 200)
        data = resp.json()
        assert data["preview_payload"]["preview_version"] == 2

    @pytest.mark.asyncio
    async def test_rollback_step_moves_current_step_back(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={"source_type": "csv", "source_locator": "packages/db/import/herbs.csv"},
        )
        run_id = create_resp.json()["id"]

        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/preview")
        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/confirm")
        resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_ingest/rollback")

        assert_status(resp, 200)
        data = resp.json()
        assert data["current_step"] == "source_ingest"


class TestPipelineKnowledgeModelMapping:
    @pytest.mark.asyncio
    async def test_map_step_returns_shared_model_preview(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={"source_type": "manual", "source_locator": "陈皮"},
        )
        run_id = create_resp.json()["id"]

        resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")

        assert_status(resp, 200)
        data = resp.json()
        assert data["preview_kind"] == "graph_mapping"
        assert data["preview_payload"]["validation"]["is_valid"] is True
        assert data["preview_payload"]["nodes"][0]["type"] == "Herb"
        assert data["preview_payload"]["nodes"][0]["label"] == "药材"

    @pytest.mark.asyncio
    async def test_invalid_map_step_cannot_be_confirmed(self, client):
        create_resp = await client.post(
            "/api/v1/pipeline/runs",
            json={"source_type": "manual", "source_locator": "   "},
        )
        run_id = create_resp.json()["id"]

        await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")
        resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/confirm")

        assert_status(resp, 400)
        assert resp.json()["detail"] == "当前映射结果未通过共享图模型校验，不能进入下一步"
