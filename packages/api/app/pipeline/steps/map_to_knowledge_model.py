from typing import Any, cast

from knowledge_model import HerbNodeModel, NODE_TYPE_LABELS
from pydantic import ValidationError

from app.pipeline.models import PipelineRun, PipelineStepKey
from .base import PipelineStepContext, build_preview_response


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


def build_map_to_knowledge_model_preview(context: PipelineStepContext):
    candidate_name = _resolve_candidate_name(context.run)

    if not candidate_name:
        return build_preview_response(
            context=context,
            step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
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
            errors=["未能生成可映射的实体名称"],
            next_step_ready=False,
        )

    try:
        herb_node = HerbNodeModel(
            id=f"herb-{candidate_name}",
            name=candidate_name,
            source=context.run.source_locator,
        )
    except ValidationError as exc:
        return build_preview_response(
            context=context,
            step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
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
            errors=[error["msg"] for error in exc.errors()],
            next_step_ready=False,
        )

    node_payload = herb_node.model_dump(mode="json")
    node_payload["label"] = NODE_TYPE_LABELS[herb_node.type]

    return build_preview_response(
        context=context,
        step=PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL,
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
        next_step_ready=True,
    )
