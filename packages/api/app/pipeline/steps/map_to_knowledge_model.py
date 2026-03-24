from typing import Any, cast

from knowledge_model import HerbNodeModel, NODE_TYPE_LABELS
from pydantic import ValidationError

from app.pipeline.models import PipelineRun, PipelineStepKey, PipelineStepStatus
from app.pipeline.schemas import PipelineStepPreviewResponse


def _resolve_candidate_name(run: PipelineRun) -> str:
    extracted_candidates = (
        run.steps[PipelineStepKey.EXTRACT].preview_payload.get("candidates", [])
        if PipelineStepKey.EXTRACT in run.steps
        else []
    )
    candidates = cast(list[Any], extracted_candidates)
    if candidates:
        first_candidate = candidates[0]
        if isinstance(first_candidate, dict):
            return str(first_candidate.get("name", "")).strip()
    return run.source_locator.strip()


def build_map_to_knowledge_model_preview(run: PipelineRun) -> PipelineStepPreviewResponse:
    candidate_name = _resolve_candidate_name(run)

    if not candidate_name:
        return PipelineStepPreviewResponse(
            run_id=run.id,
            step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
            status=PipelineStepStatus.PREVIEW_READY,
            summary="共享图模型映射未通过校验",
            preview_kind="graph_mapping",
            preview_payload={
                "nodes": [],
                "validation": {
                    "is_valid": False,
                    "passed": 0,
                    "failed": 1,
                },
            },
            warnings=[],
            errors=["未能生成可映射的实体名称"],
            artifacts=[],
            next_step_ready=False,
        )

    try:
        herb_node = HerbNodeModel(
            id=f"herb-{candidate_name}",
            name=candidate_name,
            source=run.source_locator,
        )
    except ValidationError as exc:
        return PipelineStepPreviewResponse(
            run_id=run.id,
            step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
            status=PipelineStepStatus.PREVIEW_READY,
            summary="共享图模型映射未通过校验",
            preview_kind="graph_mapping",
            preview_payload={
                "nodes": [],
                "validation": {
                    "is_valid": False,
                    "passed": 0,
                    "failed": 1,
                },
            },
            warnings=[],
            errors=[error["msg"] for error in exc.errors()],
            artifacts=[],
            next_step_ready=False,
        )

    node_payload = herb_node.model_dump(mode="json")
    node_payload["label"] = NODE_TYPE_LABELS[herb_node.type]

    return PipelineStepPreviewResponse(
        run_id=run.id,
        step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
        status=PipelineStepStatus.PREVIEW_READY,
        summary="共享图模型映射预览已生成",
        preview_kind="graph_mapping",
        preview_payload={
            "nodes": [node_payload],
            "validation": {
                "is_valid": True,
                "passed": 1,
                "failed": 0,
            },
            "boundary": "knowledge_model.HerbNodeModel",
        },
        warnings=[],
        errors=[],
        artifacts=[],
        next_step_ready=True,
    )
