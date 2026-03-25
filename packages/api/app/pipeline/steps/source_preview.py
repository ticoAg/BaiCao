from app.pipeline.models import PipelineStepKey

from .base import PipelineStepContext, build_preview_response, get_preview_records, get_source_text, source_ready


def build_source_preview_step(context: PipelineStepContext):
    descriptor = context.source_descriptor
    content_text = get_source_text(context)
    return build_preview_response(
        context=context,
        step=PipelineStepKey.SOURCE_PREVIEW,
        summary="原始内容预览已生成" if source_ready(descriptor) else "原始内容预览不可用",
        preview_kind="source_contents",
        preview_payload={
            "adapter": descriptor.adapter,
            "content_preview": content_text[:160],
            "content_text": content_text,
            "line_samples": descriptor.sample_lines,
            "sample_records": get_preview_records(context),
        },
        warnings=descriptor.warnings,
        errors=descriptor.errors,
        next_step_ready=source_ready(descriptor),
    )
