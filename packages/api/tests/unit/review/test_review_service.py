import pytest

from app.pipeline.models import PipelineStepKey, PipelineStepStatus
from app.pipeline.service import PipelineService
from app.review.models import ReviewItemDecision, ReviewSessionStatus
from app.review.service import InMemoryReviewStorage, ReviewService


@pytest.mark.asyncio
async def test_review_session_supports_item_level_edits() -> None:
    pipeline = PipelineService()
    run = await pipeline.create_run(source_type="manual", source_locator="陈皮")
    await pipeline.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)

    review_service = ReviewService(storage=InMemoryReviewStorage())
    session = await review_service.create_or_refresh_session(await pipeline.get_run(run.id))

    assert session.status == ReviewSessionStatus.DRAFT
    assert len(session.items) == 1
    item = session.items[0]
    assert item.decision == ReviewItemDecision.PENDING

    updated = await review_service.update_item(
        run_id=run.id,
        item_key=item.item_key,
        decision=ReviewItemDecision.EDIT,
        revised_payload={**item.revised_payload, "name": "陈皮炭"},
        comment="人工修订名称",
    )

    assert updated.items[0].decision == ReviewItemDecision.EDIT
    assert updated.items[0].revised_payload["name"] == "陈皮炭"

    confirmed = await review_service.confirm_session(run.id)
    assert confirmed.status == ReviewSessionStatus.CONFIRMED


@pytest.mark.asyncio
async def test_pipeline_human_review_requires_confirmed_review_session() -> None:
    review_service = ReviewService(storage=InMemoryReviewStorage())
    pipeline = PipelineService(review_service=review_service)
    run = await pipeline.create_run(source_type="manual", source_locator="陈皮")

    await pipeline.preview_step(run.id, PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL)
    await pipeline.preview_step(run.id, PipelineStepKey.HUMAN_REVIEW)

    with pytest.raises(ValueError, match="人工确认会话尚未确认"):
        await pipeline.confirm_step(run.id, PipelineStepKey.HUMAN_REVIEW)

    session = await review_service.get_session(run.id)
    await review_service.update_item(
        run_id=run.id,
        item_key=session.items[0].item_key,
        decision=ReviewItemDecision.CONFIRM,
    )
    await review_service.confirm_session(run.id)

    updated = await pipeline.confirm_step(run.id, PipelineStepKey.HUMAN_REVIEW)
    assert updated.steps[PipelineStepKey.HUMAN_REVIEW].status == PipelineStepStatus.CONFIRMED
