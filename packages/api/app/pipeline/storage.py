from app.models.pipeline import PipelineRunModel
from app.pipeline.models import PipelineRun, PipelineRunStatus, PipelineStepKey, PipelineStepState, PipelineStepStatus


def _serialize_steps(run: PipelineRun) -> dict[str, dict[str, object]]:
    return {
        step_key.value: {
            "key": state.key.value,
            "status": state.status.value,
            "summary": state.summary,
            "preview_version": state.preview_version,
        }
        for step_key, state in run.steps.items()
    }


def _deserialize_run(model: PipelineRunModel) -> PipelineRun:
    return PipelineRun(
        id=model.id,
        source_type=model.source_type,
        source_locator=model.source_locator,
        status=PipelineRunStatus(model.status),
        current_step=PipelineStepKey(model.current_step),
        steps={
            PipelineStepKey(step_key): PipelineStepState(
                key=PipelineStepKey(payload["key"]),
                status=PipelineStepStatus(payload["status"]),
                summary=payload.get("summary"),
                preview_version=payload.get("preview_version", 0),
            )
            for step_key, payload in model.steps.items()
        },
    )


class InMemoryPipelineStorage:
    def __init__(self) -> None:
        self._runs: dict[str, PipelineRun] = {}

    async def save_run(self, run: PipelineRun) -> PipelineRun:
        self._runs[run.id] = run
        return run

    async def get_run(self, run_id: str) -> PipelineRun:
        return self._runs[run_id]


class SQLAlchemyPipelineStorage:
    def __init__(self, session) -> None:
        self.session = session

    async def save_run(self, run: PipelineRun) -> PipelineRun:
        model = await self.session.get(PipelineRunModel, run.id)
        if model is None:
            model = PipelineRunModel(
                id=run.id,
                source_type=run.source_type,
                source_locator=run.source_locator,
                status=run.status.value,
                current_step=run.current_step.value,
                steps=_serialize_steps(run),
            )
            self.session.add(model)
        else:
            model.source_type = run.source_type
            model.source_locator = run.source_locator
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
