from app.pipeline.models import PipelineStepKey

from .base import PipelineStepContext, build_preview_response, extract_candidate_names, get_normalized_text


def build_extract_preview(context: PipelineStepContext):
    if context.processed_bundle is not None:
        bundle = context.processed_bundle
        return build_preview_response(
            context=context,
            step=PipelineStepKey.EXTRACT,
            summary="药典条目结构化抽取预览已生成",
            preview_kind="extraction_candidates",
            preview_payload={
                "bundle_stats": bundle.stats,
                "entry_count": bundle.stats.get("entries_processed", 0),
                "entry_titles": bundle.stats.get("entry_titles", []),
            },
            warnings=bundle.warnings,
            errors=bundle.errors,
            next_step_ready=not bundle.errors,
        )

    normalized_text = get_normalized_text(context)
    candidates = [
        {
            "name": name,
            "type": "Herb",
            "confidence": "high" if index == 0 else "medium",
            "evidence": normalized_text[:80],
        }
        for index, name in enumerate(extract_candidate_names(context))
    ]
    errors = [] if candidates else ["未能从当前来源预览中提取候选实体"]
    return build_preview_response(
        context=context,
        step=PipelineStepKey.EXTRACT,
        summary="结构化抽取预览已生成" if candidates else "结构化抽取未生成候选实体",
        preview_kind="extraction_candidates",
        preview_payload={
            "normalized_text": normalized_text,
            "candidate_count": len(candidates),
            "candidates": candidates,
        },
        warnings=context.source_descriptor.warnings,
        errors=errors,
        next_step_ready=bool(candidates),
    )
