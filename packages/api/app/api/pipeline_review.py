from fastapi import APIRouter, Depends, HTTPException, status

from app.api.pipeline_dependencies import get_pipeline_service, get_review_service
from app.pipeline.models import PipelineStepKey
from app.pipeline.service import PipelineService
from app.review.schemas import ConfirmReviewSessionRequest, ReviewItemResponse, ReviewSessionResponse, UpdateReviewItemRequest
from app.review.service import ReviewService


router = APIRouter(prefix="/pipeline", tags=["pipeline-review"])


def _serialize_review_session(session) -> ReviewSessionResponse:
    return ReviewSessionResponse(
        id=session.id,
        run_id=session.run_id,
        step=session.step.value,
        status=session.status.value,
        items=[
            ReviewItemResponse(
                item_key=item.item_key,
                node_type=item.node_type,
                original_payload=item.original_payload,
                revised_payload=item.revised_payload,
                decision=item.decision.value,
                comment=item.comment,
            )
            for item in session.items
        ],
        comment=session.comment,
        confirmed_at=session.confirmed_at.isoformat() if session.confirmed_at else None,
    )


@router.post("/runs/{run_id}/review-session", response_model=ReviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_review_session(
    run_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    review_service: ReviewService = Depends(get_review_service),
):
    try:
        run = await pipeline_service.get_run(run_id)
        session = await review_service.create_or_refresh_session(run)
        return _serialize_review_session(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{run_id}/review-session", response_model=ReviewSessionResponse)
async def get_review_session(
    run_id: str,
    review_service: ReviewService = Depends(get_review_service),
):
    try:
        return _serialize_review_session(await review_service.get_session(run_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Review session for run '{run_id}' not found") from exc


@router.patch("/runs/{run_id}/review-session/items/{item_key}", response_model=ReviewSessionResponse)
async def update_review_item(
    run_id: str,
    item_key: str,
    payload: UpdateReviewItemRequest,
    review_service: ReviewService = Depends(get_review_service),
):
    try:
        session = await review_service.update_item(
            run_id=run_id,
            item_key=item_key,
            decision=payload.decision,
            revised_payload=payload.revised_payload,
            comment=payload.comment,
        )
        return _serialize_review_session(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Review item '{item_key}' not found") from exc


@router.post("/runs/{run_id}/review-session/confirm", response_model=ReviewSessionResponse)
async def confirm_review_session(
    run_id: str,
    payload: ConfirmReviewSessionRequest,
    review_service: ReviewService = Depends(get_review_service),
):
    try:
        session = await review_service.confirm_session(run_id, comment=payload.comment)
        return _serialize_review_session(session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Review session for run '{run_id}' not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{run_id}/steps/{step}/ensure-review-preview", response_model=dict)
async def ensure_review_preview(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    if step != PipelineStepKey.HUMAN_REVIEW:
        raise HTTPException(status_code=400, detail="Only the human_review step supports review previews")
    preview = await pipeline_service.preview_step(run_id, PipelineStepKey.HUMAN_REVIEW)
    return preview.model_dump(mode="json")
