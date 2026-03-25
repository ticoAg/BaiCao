import pytest

from app.export.models import ExportRecordStatus, GraphWriteStatus
from app.export.service import (
    ExportService,
    FailingGraphWriter,
    InMemoryExportStorage,
    InMemoryGraphWriter,
)
from app.pipeline.models import PipelineStepKey
from app.pipeline.service import PipelineService
from app.review.models import ReviewItemDecision
from app.review.service import InMemoryReviewStorage, ReviewService
from app.storage.objects.memory import InMemoryObjectStorage


@pytest.mark.asyncio
async def test_execute_export_writes_snapshot_before_graph() -> None:
    review_service = ReviewService(storage=InMemoryReviewStorage())
    export_storage = InMemoryExportStorage()
    object_storage = InMemoryObjectStorage()
    export_service = ExportService(
        storage=export_storage,
        review_service=review_service,
        object_storage=object_storage,
        graph_writer=FailingGraphWriter(RuntimeError("neo4j unavailable")),
    )
    pipeline = PipelineService(review_service=review_service, export_service=export_service)
    run = await pipeline.create_run(source_type="manual", source_locator="陈皮")
    await pipeline.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    session = await review_service.create_or_refresh_session(await pipeline.get_run(run.id))
    await review_service.update_item(
        run_id=run.id,
        item_key=session.items[0].item_key,
        decision=ReviewItemDecision.CONFIRM,
    )
    await review_service.confirm_session(run.id)

    await pipeline.confirm_step(run.id, PipelineStepKey.HUMAN_REVIEW)
    await pipeline.preview_step(run.id, PipelineStepKey.EXPORT)
    await pipeline.confirm_step(run.id, PipelineStepKey.EXPORT)

    record = await export_service.execute_export(await pipeline.get_run(run.id))

    assert record.status == ExportRecordStatus.PARTIAL_FAILED
    assert record.graph_write_status == GraphWriteStatus.FAILED
    assert record.snapshot_bucket is not None
    assert record.snapshot_object_key is not None
    assert object_storage.get_object(record.snapshot_bucket, record.snapshot_object_key).startswith(b'{"node_type"')


@pytest.mark.asyncio
async def test_retry_graph_write_reuses_snapshot() -> None:
    review_service = ReviewService(storage=InMemoryReviewStorage())
    export_storage = InMemoryExportStorage()
    object_storage = InMemoryObjectStorage()
    failing = ExportService(
        storage=export_storage,
        review_service=review_service,
        object_storage=object_storage,
        graph_writer=FailingGraphWriter(RuntimeError("neo4j unavailable")),
    )
    pipeline = PipelineService(review_service=review_service, export_service=failing)
    run = await pipeline.create_run(source_type="manual", source_locator="陈皮")
    await pipeline.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    session = await review_service.create_or_refresh_session(await pipeline.get_run(run.id))
    await review_service.update_item(
        run_id=run.id,
        item_key=session.items[0].item_key,
        decision=ReviewItemDecision.CONFIRM,
    )
    await review_service.confirm_session(run.id)

    await pipeline.confirm_step(run.id, PipelineStepKey.HUMAN_REVIEW)
    await pipeline.preview_step(run.id, PipelineStepKey.EXPORT)
    await pipeline.confirm_step(run.id, PipelineStepKey.EXPORT)

    failed_record = await failing.execute_export(await pipeline.get_run(run.id))

    succeeding_writer = InMemoryGraphWriter()
    succeeding = ExportService(
        storage=export_storage,
        review_service=review_service,
        object_storage=object_storage,
        graph_writer=succeeding_writer,
    )

    retried = await succeeding.retry_graph_write(failed_record.id)

    assert retried.status == ExportRecordStatus.COMPLETED
    assert retried.graph_write_status == GraphWriteStatus.SUCCEEDED
    assert retried.retry_count == 1
    assert succeeding_writer.records[0].node_name == "陈皮"
