from app.pipeline.models import PipelineStepKey

from .base import PipelineStepContext, build_preview_response, source_ready


def build_source_ingest_preview(context: PipelineStepContext):
    descriptor = context.source_descriptor
    return build_preview_response(
        context=context,
        step=PipelineStepKey.SOURCE_INGEST,
        summary="来源接入预览已生成" if source_ready(descriptor) else "来源接入预览存在阻塞",
        preview_kind="source_descriptor",
        preview_payload={
            "adapter": descriptor.adapter,
            "source_type": descriptor.source_type,
            "source_locator": context.run.source_locator,
            "source_summary": descriptor.source_summary,
            "sample_lines": descriptor.sample_lines,
            "metadata": descriptor.metadata,
        },
        warnings=descriptor.warnings,
        errors=descriptor.errors,
        next_step_ready=source_ready(descriptor),
    )
