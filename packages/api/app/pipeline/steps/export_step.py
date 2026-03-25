from .base import PipelineStepContext, build_preview_response
from app.pipeline.models import PipelineStepKey


def build_export_preview(context: PipelineStepContext):
    mapping_payload = context.run.steps[PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL].preview_payload
    validation = mapping_payload.get("validation", {})
    is_valid = validation.get("is_valid") is True
    nodes = mapping_payload.get("nodes", [])
    errors = [] if is_valid else ["共享模型映射未通过校验，导出预览仅显示占位结果"]
    return build_preview_response(
        context=context,
        step=PipelineStepKey.EXPORT,
        summary="导出/入库预览已生成" if is_valid else "导出/入库预览存在阻塞",
        preview_kind="export_plan",
        preview_payload={
            "export_targets": ["neo4j", "jsonl_snapshot"],
            "record_count": len(nodes),
            "records": nodes,
        },
        errors=errors,
        next_step_ready=is_valid,
    )
