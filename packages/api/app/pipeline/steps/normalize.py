from app.pipeline.models import PipelineStepKey

from .base import PipelineStepContext, build_preview_response, get_source_text, source_ready


def build_normalize_preview(context: PipelineStepContext):
    original_text = get_source_text(context)
    normalized_text = (
        original_text.replace("：", ":").replace("；", ";").replace("。", "。 ").replace("\n", " ").strip()
    )
    while "  " in normalized_text:
        normalized_text = normalized_text.replace("  ", " ")

    return build_preview_response(
        context=context,
        step=PipelineStepKey.NORMALIZE,
        summary="规范化清洗预览已生成" if normalized_text else "规范化清洗未得到内容",
        preview_kind="normalized_content",
        preview_payload={
            "normalized_text": normalized_text,
            "normalization_notes": [
                "统一空白符",
                "保留来源文本顺序",
            ],
            "source_excerpt": original_text[:120],
        },
        warnings=context.source_descriptor.warnings,
        errors=context.source_descriptor.errors,
        next_step_ready=source_ready(context.source_descriptor) and bool(normalized_text),
    )
