from fastapi import APIRouter, Depends, HTTPException, status

from app.api.pipeline_dependencies import get_export_service, get_pipeline_service
from app.export.schemas import ExportPlanResponse, ExportRecordResponse
from app.export.service import ExportService
from app.pipeline.service import PipelineService


router = APIRouter(prefix="/pipeline", tags=["pipeline-export"])


def _serialize_export_record(record) -> ExportRecordResponse:
    return ExportRecordResponse(
        id=record.id,
        run_id=record.run_id,
        review_session_id=record.review_session_id,
        status=record.status.value,
        graph_write_status=record.graph_write_status.value,
        snapshot_bucket=record.snapshot_bucket,
        snapshot_object_key=record.snapshot_object_key,
        snapshot_checksum=record.snapshot_checksum,
        snapshot_size=record.snapshot_size,
        error_message=record.error_message,
        retry_count=record.retry_count,
    )


@router.post("/runs/{run_id}/export-plan", response_model=ExportPlanResponse)
async def build_export_plan(
    run_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    export_service: ExportService = Depends(get_export_service),
):
    try:
        run = await pipeline_service.get_run(run_id)
        return await export_service.build_export_plan_payload(run)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc


@router.post("/runs/{run_id}/export-executions", response_model=ExportRecordResponse, status_code=status.HTTP_201_CREATED)
async def execute_export(
    run_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    export_service: ExportService = Depends(get_export_service),
):
    try:
        run = await pipeline_service.get_run(run_id)
        return _serialize_export_record(await export_service.execute_export(run))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{run_id}' not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{run_id}/export-executions/latest", response_model=ExportRecordResponse)
async def get_latest_export_execution(
    run_id: str,
    export_service: ExportService = Depends(get_export_service),
):
    record = await export_service.get_latest_record(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Export execution for run '{run_id}' not found")
    return _serialize_export_record(record)


@router.post("/runs/{run_id}/export-executions/{export_id}/retry-graph-write", response_model=ExportRecordResponse)
async def retry_graph_write(
    run_id: str,
    export_id: str,
    export_service: ExportService = Depends(get_export_service),
):
    try:
        record = await export_service.retry_graph_write(export_id)
        if record.run_id != run_id:
            raise HTTPException(status_code=404, detail=f"Export execution '{export_id}' not found for run '{run_id}'")
        return _serialize_export_record(record)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Export execution '{export_id}' not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
