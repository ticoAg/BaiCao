from typing import Any, cast

from app.pipeline.adapters import build_source_adapters, get_source_adapter
from app.review.service import ReviewService
from app.export.service import ExportService
from app.pipeline.models import (
    PIPELINE_STEP_ORDER,
    PipelineRun,
    PipelineRunStatus,
    PipelineStepKey,
    PipelineStepState,
    PipelineStepStatus,
)
from app.pipeline.schemas import PipelineArtifactReference, PipelineStepPreviewResponse
from app.pipeline.steps import STEP_HANDLERS, PipelineStepContext
from app.pipeline.storage import InMemoryPipelineStorage, PipelineStorage


class PipelineService:
    def __init__(
        self,
        storage: PipelineStorage | None = None,
        review_service: ReviewService | None = None,
        export_service: ExportService | None = None,
    ) -> None:
        self.storage = storage or InMemoryPipelineStorage()
        self.source_adapters = build_source_adapters()
        self.review_service = review_service
        self.export_service = export_service

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

    async def list_runs(self) -> list[PipelineRun]:
        return await self.storage.list_runs()

    async def preview_step(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse:
        run = await self.get_run(run_id)
        step_state = run.steps[step]
        preview_response = await self._build_preview_response(run, step)
        step_state.status = preview_response.status
        step_state.preview_version += 1
        step_state.summary = preview_response.summary
        step_state.preview_kind = preview_response.preview_kind
        step_state.preview_payload = preview_response.preview_payload
        step_state.warnings = preview_response.warnings
        step_state.errors = preview_response.errors
        run.status = PipelineRunStatus.PENDING_REVIEW
        preview_response.preview_payload["preview_version"] = step_state.preview_version
        preview_response.artifacts = [
            PipelineArtifactReference(
                key=f"{step.value}-preview-v{step_state.preview_version}",
                label=f"{step.value} 预览快照 v{step_state.preview_version}",
                uri=None,
            )
        ]
        await self.storage.save_run(run)
        await self.storage.save_preview_artifact(preview_response)
        return preview_response

    async def confirm_step(self, run_id: str, step: PipelineStepKey) -> PipelineRun:
        run = await self.get_run(run_id)
        step_state = run.steps[step]
        if step == PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL:
            validation = cast(dict[str, Any], step_state.preview_payload.get("validation", {}))
            if not validation or validation.get("is_valid") is not True:
                raise ValueError("当前映射结果未通过共享图模型校验，不能进入下一步")
        if step == PipelineStepKey.HUMAN_REVIEW:
            if self.review_service is None:
                raise ValueError("人工确认服务不可用，不能锁定当前步骤")
            review_session = await self.review_service.get_session(run_id)
            if review_session.status.value != "confirmed":
                raise ValueError("人工确认会话尚未确认，不能进入下一步")
        step_state.status = PipelineStepStatus.CONFIRMED
        step_state.summary = f"{step} confirmed"

        current_index = PIPELINE_STEP_ORDER.index(step)
        if current_index + 1 < len(PIPELINE_STEP_ORDER):
            run.current_step = PIPELINE_STEP_ORDER[current_index + 1]
            run.status = PipelineRunStatus.RUNNING
        else:
            run.status = PipelineRunStatus.COMPLETED

        return await self.storage.save_run(run)

    async def rerun_step(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse:
        return await self.preview_step(run_id, step)

    async def rollback_to_step(self, run_id: str, step: PipelineStepKey) -> PipelineRun:
        run = await self.get_run(run_id)
        rollback_index = PIPELINE_STEP_ORDER.index(step)

        for index, step_key in enumerate(PIPELINE_STEP_ORDER):
            if index >= rollback_index:
                run.steps[step_key].status = PipelineStepStatus.PENDING
                run.steps[step_key].summary = None
                run.steps[step_key].preview_kind = None
                run.steps[step_key].preview_payload = {}
                run.steps[step_key].warnings = []
                run.steps[step_key].errors = []
                if index == rollback_index:
                    run.steps[step_key].preview_version = 0

        run.current_step = step
        run.status = PipelineRunStatus.RUNNING
        return await self.storage.save_run(run)

    async def get_latest_preview(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse:
        preview = await self.storage.get_latest_preview(run_id, step)
        if preview is None:
            raise KeyError(f"Preview for step '{step.value}' not found")
        return preview

    async def list_preview_artifacts(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> list[PipelineStepPreviewResponse]:
        return await self.storage.list_preview_artifacts(run_id, step)

    async def _build_preview_response(
        self,
        run: PipelineRun,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse:
        source_adapter = get_source_adapter(run.source_type, self.source_adapters)
        source_descriptor = source_adapter.describe(run.source_locator)
        context = PipelineStepContext(
            run=run,
            source_descriptor=source_descriptor,
        )
        if step == PipelineStepKey.HUMAN_REVIEW and self.review_service is not None:
            return await self.review_service.build_preview(run, context)
        if step == PipelineStepKey.EXPORT and self.export_service is not None:
            return await self.export_service.build_preview(run, context)
        handler = STEP_HANDLERS[step]
        return handler(context)
