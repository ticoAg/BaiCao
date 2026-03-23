from app.pipeline.models import (
    PIPELINE_STEP_ORDER,
    PipelineRun,
    PipelineRunStatus,
    PipelineStepKey,
    PipelineStepState,
    PipelineStepStatus,
)
from app.pipeline.schemas import PipelineStepPreviewResponse
from app.pipeline.storage import InMemoryPipelineStorage


class PipelineService:
    def __init__(self, storage: InMemoryPipelineStorage | None = None) -> None:
        self.storage = storage or InMemoryPipelineStorage()

    async def create_run(self, source_type: str, source_locator: str) -> PipelineRun:
        steps = {
            key: PipelineStepState(key=key)
            for key in PIPELINE_STEP_ORDER
        }
        run = PipelineRun(
            source_type=source_type,
            source_locator=source_locator,
            status=PipelineRunStatus.PENDING,
            current_step=PipelineStepKey.SOURCE_INGEST,
            steps=steps,
        )
        return await self.storage.save_run(run)

    async def get_run(self, run_id: str) -> PipelineRun:
        return await self.storage.get_run(run_id)

    async def preview_step(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse:
        run = await self.get_run(run_id)
        step_state = run.steps[step]
        step_state.status = PipelineStepStatus.PREVIEW_READY
        step_state.preview_version += 1
        step_state.summary = f"{step} preview ready"
        run.status = PipelineRunStatus.PENDING_REVIEW
        await self.storage.save_run(run)

        return PipelineStepPreviewResponse(
            run_id=run.id,
            step=step,
            status=PipelineStepStatus.PREVIEW_READY,
            summary="步骤预览已生成",
            preview_kind="summary",
            preview_payload={
                "source_type": run.source_type,
                "source_locator": run.source_locator,
                "step": step.value,
                "preview_version": step_state.preview_version,
            },
            warnings=[],
            errors=[],
            artifacts=[],
            next_step_ready=False,
        )

    async def confirm_step(self, run_id: str, step: PipelineStepKey) -> PipelineRun:
        run = await self.get_run(run_id)
        step_state = run.steps[step]
        step_state.status = PipelineStepStatus.CONFIRMED
        step_state.summary = f"{step} confirmed"

        current_index = PIPELINE_STEP_ORDER.index(step)
        if current_index + 1 < len(PIPELINE_STEP_ORDER):
            run.current_step = PIPELINE_STEP_ORDER[current_index + 1]
            run.status = PipelineRunStatus.RUNNING
        else:
            run.status = PipelineRunStatus.COMPLETED

        return await self.storage.save_run(run)
