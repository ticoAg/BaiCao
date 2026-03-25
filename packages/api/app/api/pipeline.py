from fastapi import APIRouter, Depends, HTTPException, status

from .pipeline_dependencies import get_pipeline_service
from ..pipeline.schemas import (
    CreatePipelineRunRequest,
    PipelineRunResponse,
    PipelineStepPreviewResponse,
)
from ..pipeline.service import PipelineService
from ..pipeline.models import PipelineStepKey


router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _serialize_run(run) -> PipelineRunResponse:
    return PipelineRunResponse(
        id=run.id,
        source_type=run.source_type,
        source_locator=run.source_locator,
        status=run.status.value,
        current_step=run.current_step.value,
        steps={
            step_key.value: {
                "key": state.key.value,
                "status": state.status.value,
                "summary": state.summary,
                "preview_version": state.preview_version,
                "preview_kind": state.preview_kind,
                "preview_payload": state.preview_payload,
                "warnings": state.warnings,
                "errors": state.errors,
            }
            for step_key, state in run.steps.items()
        },
    )


@router.post("/runs", response_model=PipelineRunResponse, status_code=status.HTTP_201_CREATED)
async def create_pipeline_run(
    payload: CreatePipelineRunRequest,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    run = await pipeline_service.create_run(
        source_type=payload.source_type,
        source_locator=payload.source_locator,
    )
    return _serialize_run(run)


@router.get("/runs", response_model=list[PipelineRunResponse])
async def list_pipeline_runs(
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    runs = await pipeline_service.list_runs()
    return [_serialize_run(run) for run in runs]


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline_run(
    run_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        run = await pipeline_service.get_run(run_id)
        return _serialize_run(run)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc


@router.post("/runs/{run_id}/steps/{step}/preview", response_model=PipelineStepPreviewResponse)
async def preview_pipeline_step(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        return await pipeline_service.preview_step(run_id, step)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc


@router.get("/runs/{run_id}/steps/{step}/preview", response_model=PipelineStepPreviewResponse)
async def get_latest_pipeline_step_preview(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        return await pipeline_service.get_latest_preview(run_id, step)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/steps/{step}/artifacts", response_model=list[PipelineStepPreviewResponse])
async def list_pipeline_step_artifacts(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        return await pipeline_service.list_preview_artifacts(run_id, step)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/{run_id}/steps/{step}/confirm", response_model=PipelineRunResponse)
async def confirm_pipeline_step(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        run = await pipeline_service.confirm_step(run_id, step)
        return _serialize_run(run)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/runs/{run_id}/steps/{step}/rerun", response_model=PipelineStepPreviewResponse)
async def rerun_pipeline_step(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        return await pipeline_service.rerun_step(run_id, step)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc


@router.post("/runs/{run_id}/steps/{step}/rollback", response_model=PipelineRunResponse)
async def rollback_pipeline_step(
    run_id: str,
    step: PipelineStepKey,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
):
    try:
        run = await pipeline_service.rollback_to_step(run_id, step)
        return _serialize_run(run)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc
