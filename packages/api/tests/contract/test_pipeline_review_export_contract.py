import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.pipeline_dependencies import get_export_service, get_pipeline_service, get_review_service
from app.export.service import ExportService, InMemoryExportStorage, InMemoryGraphWriter
from app.pipeline.service import PipelineService
from app.pipeline.storage import InMemoryPipelineStorage
from app.review.service import InMemoryReviewStorage, ReviewService
from app.storage.objects.memory import InMemoryObjectStorage


@pytest.fixture
async def client():
    pipeline_storage = InMemoryPipelineStorage()
    review_service = ReviewService(storage=InMemoryReviewStorage())
    export_service = ExportService(
        storage=InMemoryExportStorage(),
        review_service=review_service,
        object_storage=InMemoryObjectStorage(),
        graph_writer=InMemoryGraphWriter(),
    )
    pipeline_service = PipelineService(
        storage=pipeline_storage,
        review_service=review_service,
        export_service=export_service,
    )

    app.dependency_overrides[get_review_service] = lambda: review_service
    app.dependency_overrides[get_export_service] = lambda: export_service
    app.dependency_overrides[get_pipeline_service] = lambda: pipeline_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_review_and_export_contract_requires_explicit_execute(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/pipeline/runs",
        json={"source_type": "manual", "source_locator": "陈皮"},
    )
    assert create_resp.status_code == 201
    run_id = create_resp.json()["id"]

    mapping_resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/map_to_knowledge_model/preview")
    assert mapping_resp.status_code == 200
    assert mapping_resp.json()["preview_payload"]["validation"]["is_valid"] is True

    review_create = await client.post(f"/api/v1/pipeline/runs/{run_id}/review-session")
    assert review_create.status_code == 201
    item_key = review_create.json()["items"][0]["item_key"]

    review_patch = await client.patch(
        f"/api/v1/pipeline/runs/{run_id}/review-session/items/{item_key}",
        json={"decision": "edit", "revised_payload": {"id": "herb-陈皮炭", "name": "陈皮炭", "type": "Herb", "label": "药材", "source": "陈皮"}},
    )
    assert review_patch.status_code == 200
    assert review_patch.json()["items"][0]["decision"] == "edit"

    review_confirm = await client.post(f"/api/v1/pipeline/runs/{run_id}/review-session/confirm", json={})
    assert review_confirm.status_code == 200
    assert review_confirm.json()["status"] == "confirmed"

    human_confirm = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/human_review/confirm")
    assert human_confirm.status_code == 200
    assert human_confirm.json()["current_step"] == "export"

    export_plan = await client.post(f"/api/v1/pipeline/runs/{run_id}/export-plan")
    assert export_plan.status_code == 200
    assert export_plan.json()["record_count"] == 1
    assert export_plan.json()["records"][0]["node_name"] == "陈皮炭"

    latest_before_execute = await client.get(f"/api/v1/pipeline/runs/{run_id}/export-executions/latest")
    assert latest_before_execute.status_code == 404

    export_preview = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/export/preview")
    assert export_preview.status_code == 200
    assert export_preview.json()["preview_kind"] == "export_plan"

    export_confirm = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/export/confirm")
    assert export_confirm.status_code == 200
    assert export_confirm.json()["status"] == "completed"

    export_execute = await client.post(f"/api/v1/pipeline/runs/{run_id}/export-executions")
    assert export_execute.status_code == 201
    assert export_execute.json()["status"] == "completed"
    assert export_execute.json()["graph_write_status"] == "succeeded"

    latest_after_execute = await client.get(f"/api/v1/pipeline/runs/{run_id}/export-executions/latest")
    assert latest_after_execute.status_code == 200
    assert latest_after_execute.json()["snapshot_object_key"].endswith("/snapshot.jsonl")
