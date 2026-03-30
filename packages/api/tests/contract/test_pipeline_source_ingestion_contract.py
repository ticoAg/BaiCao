import pytest
from httpx import ASGITransport, AsyncClient

from app.api.pipeline_dependencies import get_export_service, get_pipeline_service, get_review_service
from app.export.service import ExportService, InMemoryExportStorage, InMemoryGraphWriter
from app.main import app
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
async def test_create_run_accepts_structured_source(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/pipeline/runs",
        json={
            "source_type": "huggingface_repo",
            "source_locator": "ZJUFanLab/TCMChat-dataset-600k",
            "source_payload": {
                "source_type": "huggingface_repo",
                "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
            },
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["source_type"] == "huggingface_repo"
    assert data["source_payload"]["source_input"]["repo_id"] == "ZJUFanLab/TCMChat-dataset-600k"
