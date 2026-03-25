from .base import PipelineStepContext, build_preview_response
from app.pipeline.models import PipelineStepKey


def build_human_review_preview(context: PipelineStepContext):
    mapping_payload = context.run.steps[PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL].preview_payload
    validation = mapping_payload.get("validation", {})
    is_valid = validation.get("is_valid") is True
    review_items = []
    if is_valid:
        for node in mapping_payload.get("nodes", []):
            review_items.append(
                {
                    "name": node.get("name"),
                    "type": node.get("type"),
                    "recommended_action": "confirm",
                    "status": "requires_confirmation",
                }
            )

    blocking_issues = [] if is_valid else ["共享模型映射未通过校验，需先修正候选实体"]
    return build_preview_response(
        context=context,
        step=PipelineStepKey.HUMAN_REVIEW,
        summary="人工确认清单已生成" if is_valid else "人工确认前仍有阻塞项",
        preview_kind="review_decision",
        preview_payload={
            "review_items": review_items,
            "blocking_issues": blocking_issues,
        },
        errors=blocking_issues,
        next_step_ready=is_valid,
    )
