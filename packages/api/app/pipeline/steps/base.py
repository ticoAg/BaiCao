from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from data_ingestion.bundles import UnifiedGraphBundle

from app.pipeline.adapters import SourceDescriptor
from app.pipeline.materialization import MaterializedSource
from app.pipeline.models import PipelineRun, PipelineStepKey, PipelineStepStatus
from app.pipeline.schemas import PipelineStepPreviewResponse


@dataclass(frozen=True)
class PipelineStepContext:
    run: PipelineRun
    source_descriptor: SourceDescriptor
    materialized_source: MaterializedSource | None = None
    processed_bundle: UnifiedGraphBundle | None = None


StepHandler = Callable[[PipelineStepContext], PipelineStepPreviewResponse]

STOPWORDS = {"候选实体", "药材", "归经", "功效", "来源", "数据集", "节点"}


def build_preview_response(
    *,
    context: PipelineStepContext,
    step: PipelineStepKey,
    summary: str,
    preview_kind: str,
    preview_payload: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    next_step_ready: bool = False,
) -> PipelineStepPreviewResponse:
    return PipelineStepPreviewResponse(
        run_id=context.run.id,
        step=step,
        status=PipelineStepStatus.PREVIEW_READY,
        summary=summary,
        preview_kind=preview_kind,
        preview_payload=preview_payload,
        warnings=warnings or [],
        errors=errors or [],
        artifacts=[],
        next_step_ready=next_step_ready,
    )


def source_ready(source_descriptor: SourceDescriptor) -> bool:
    source_summary = source_descriptor.source_summary
    if source_descriptor.errors:
        return False
    if source_summary.get("exists") is False:
        return False
    if source_summary.get("is_valid") is False:
        return False
    return True


def get_source_text(context: PipelineStepContext) -> str:
    if context.materialized_source is not None:
        if context.materialized_source.readme_content:
            return context.materialized_source.readme_content.strip()
        for candidate in context.materialized_source.candidate_files:
            path = Path(candidate)
            if path.exists():
                return path.read_text(encoding="utf-8").strip()
    if context.source_descriptor.raw_text:
        return context.source_descriptor.raw_text.strip()
    if context.source_descriptor.sample_lines:
        return "\n".join(context.source_descriptor.sample_lines).strip()
    return context.run.source_locator.strip()


def get_normalized_text(context: PipelineStepContext) -> str:
    existing = context.run.steps[PipelineStepKey.NORMALIZE].preview_payload.get("normalized_text")
    if isinstance(existing, str) and existing.strip():
        return existing

    text = get_source_text(context)
    normalized = text.replace("：", ":").replace("；", ";").replace("。", "。 ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def get_preview_records(context: PipelineStepContext) -> list[dict[str, Any]]:
    preview_records = context.source_descriptor.metadata.get("preview_records", [])
    if isinstance(preview_records, list):
        return [record for record in preview_records if isinstance(record, dict)]
    return []


def extract_candidate_names(context: PipelineStepContext) -> list[str]:
    records = get_preview_records(context)
    names: list[str] = []
    for record in records:
        name = str(record.get("node_name") or record.get("name") or "").strip()
        if name:
            names.append(name)

    if names:
        return names

    text = get_normalized_text(context)
    match = re.search(r"候选实体[:：]\s*([一-龥]{1,12})", text)
    if match:
        return [match.group(1)]

    match = re.search(r"([一-龥]{1,12})[（(](?:药材|Herb)[)）]", text)
    if match:
        return [match.group(1)]

    seen: list[str] = []
    for token in re.findall(r"[一-龥]{2,12}", text):
        if token in STOPWORDS:
            continue
        if any(stopword in token for stopword in STOPWORDS):
            continue
        if token not in seen:
            seen.append(token)
    return seen
