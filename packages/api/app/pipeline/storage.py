from typing import Any, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline import PipelineRunModel, PipelineStepArtifactModel
from app.pipeline.models import (
    PipelineRun,
    PipelineRunStatus,
    PipelineStepKey,
    PipelineStepState,
    PipelineStepStatus,
)
from app.pipeline.schemas import PipelineArtifactReference, PipelineStepPreviewResponse


class PipelineStorage(Protocol):
    async def save_run(self, run: PipelineRun) -> PipelineRun: ...
    async def get_run(self, run_id: str) -> PipelineRun: ...
    async def list_runs(self) -> list[PipelineRun]: ...
    async def save_preview_artifact(
        self,
        preview: PipelineStepPreviewResponse,
    ) -> PipelineStepPreviewResponse: ...
    async def get_latest_preview(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse | None: ...
    async def list_preview_artifacts(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> list[PipelineStepPreviewResponse]: ...


def _serialize_steps(run: PipelineRun) -> dict[str, dict[str, Any]]:
    return {
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
    }


def _deserialize_run(model: PipelineRunModel) -> PipelineRun:
    return PipelineRun(
        id=model.id,
        source_type=model.source_type,
        source_locator=model.source_locator,
        source_payload=model.source_payload,
        status=PipelineRunStatus(model.status),
        current_step=PipelineStepKey(model.current_step),
        steps={
            PipelineStepKey(step_key): PipelineStepState(
                key=PipelineStepKey(payload["key"]),
                status=PipelineStepStatus(payload["status"]),
                summary=payload.get("summary"),
                preview_version=payload.get("preview_version", 0),
                preview_kind=payload.get("preview_kind"),
                preview_payload=payload.get("preview_payload", {}),
                warnings=payload.get("warnings", []),
                errors=payload.get("errors", []),
            )
            for step_key, payload in model.steps.items()
        },
    )


def _deserialize_preview(model: PipelineStepArtifactModel) -> PipelineStepPreviewResponse:
    return PipelineStepPreviewResponse(
        run_id=model.run_id,
        step=PipelineStepKey(model.step),
        status=PipelineStepStatus(model.status),
        summary=model.summary,
        preview_kind=model.preview_kind,
        preview_payload=model.preview_payload,
        warnings=list(model.warnings or []),
        errors=list(model.errors or []),
        artifacts=[
            PipelineArtifactReference.model_validate(artifact)
            for artifact in (model.artifacts or [])
        ],
        next_step_ready=model.next_step_ready,
    )


class InMemoryPipelineStorage:
    def __init__(self) -> None:
        self._runs: dict[str, PipelineRun] = {}
        self._artifacts: dict[tuple[str, PipelineStepKey], list[PipelineStepPreviewResponse]] = {}

    async def save_run(self, run: PipelineRun) -> PipelineRun:
        self._runs[run.id] = run
        return run

    async def get_run(self, run_id: str) -> PipelineRun:
        return self._runs[run_id]

    async def list_runs(self) -> list[PipelineRun]:
        return list(reversed(list(self._runs.values())))

    async def save_preview_artifact(
        self,
        preview: PipelineStepPreviewResponse,
    ) -> PipelineStepPreviewResponse:
        key = (preview.run_id, preview.step)
        self._artifacts.setdefault(key, []).append(preview.model_copy(deep=True))
        return preview

    async def get_latest_preview(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse | None:
        artifacts = self._artifacts.get((run_id, step), [])
        if not artifacts:
            return None
        return artifacts[-1].model_copy(deep=True)

    async def list_preview_artifacts(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> list[PipelineStepPreviewResponse]:
        return [artifact.model_copy(deep=True) for artifact in reversed(self._artifacts.get((run_id, step), []))]


class SQLAlchemyPipelineStorage:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_run(self, run: PipelineRun) -> PipelineRun:
        model = await self.session.get(PipelineRunModel, run.id)
        if model is None:
            model = PipelineRunModel(
                id=run.id,
                source_type=run.source_type,
                source_locator=run.source_locator,
                source_payload=run.source_payload,
                status=run.status.value,
                current_step=run.current_step.value,
                steps=_serialize_steps(run),
            )
            self.session.add(model)
        else:
            model.source_type = run.source_type
            model.source_locator = run.source_locator
            model.source_payload = run.source_payload
            model.status = run.status.value
            model.current_step = run.current_step.value
            model.steps = _serialize_steps(run)

        await self.session.commit()
        return run

    async def get_run(self, run_id: str) -> PipelineRun:
        model = await self.session.get(PipelineRunModel, run_id)
        if model is None:
            raise KeyError(run_id)
        return _deserialize_run(model)

    async def list_runs(self) -> list[PipelineRun]:
        stmt = select(PipelineRunModel).order_by(PipelineRunModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [_deserialize_run(model) for model in result.scalars().all()]

    async def save_preview_artifact(
        self,
        preview: PipelineStepPreviewResponse,
    ) -> PipelineStepPreviewResponse:
        model = PipelineStepArtifactModel(
            run_id=preview.run_id,
            step=preview.step.value,
            preview_version=int(preview.preview_payload.get("preview_version") or 0),
            status=preview.status.value,
            summary=preview.summary,
            preview_kind=preview.preview_kind,
            preview_payload=preview.preview_payload,
            warnings=preview.warnings,
            errors=preview.errors,
            artifacts=[artifact.model_dump(mode="json") for artifact in preview.artifacts],
            next_step_ready=preview.next_step_ready,
        )
        self.session.add(model)
        await self.session.commit()
        return preview

    async def get_latest_preview(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> PipelineStepPreviewResponse | None:
        stmt = (
            select(PipelineStepArtifactModel)
            .where(
                PipelineStepArtifactModel.run_id == run_id,
                PipelineStepArtifactModel.step == step.value,
            )
            .order_by(PipelineStepArtifactModel.preview_version.desc(), PipelineStepArtifactModel.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _deserialize_preview(model)

    async def list_preview_artifacts(
        self,
        run_id: str,
        step: PipelineStepKey,
    ) -> list[PipelineStepPreviewResponse]:
        stmt = (
            select(PipelineStepArtifactModel)
            .where(
                PipelineStepArtifactModel.run_id == run_id,
                PipelineStepArtifactModel.step == step.value,
            )
            .order_by(PipelineStepArtifactModel.preview_version.desc(), PipelineStepArtifactModel.id.desc())
        )
        result = await self.session.execute(stmt)
        return [_deserialize_preview(model) for model in result.scalars().all()]
