from __future__ import annotations

from pathlib import Path
from typing import Any

from data_ingestion.bundles import UnifiedGraphBundle
from data_ingestion.routing import FileRouteKey, ProcessorRegistry
from data_ingestion.source_models import RawEntryBlock, SourceFileContext
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.shared import (
    DATASET_NAME,
    PHARMACOPOEIA_2022_FILE_PATH,
    PHARMACOPOEIA_2022_ROUTE_KEY,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.extraction_models import (
    PharmacopoeiaExtractionResult,
    PharmacopoeiaHerbExtraction,
    PharmacopoeiaPreparedPieceExtraction,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.mapping import (
    build_pharmacopoeia_bundle,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.normalization import (
    normalize_flavors_and_nature,
    normalize_meridians,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.parsing import (
    parse_pharmacopoeia_entry,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.prompts import (
    PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.segmentation import (
    segment_pharmacopoeia_entries,
)

from app.pipeline.materialization import MaterializedSource
from app.pipeline.models import PipelineRun
from app.pipeline.structured_extraction import PipelineStructuredExtractionClient


class Pharmacopoeia2022Processor:
    route_key = PHARMACOPOEIA_2022_ROUTE_KEY

    def segment(self, context: SourceFileContext) -> list[RawEntryBlock]:
        return segment_pharmacopoeia_entries(context)

    def process_entry(self, block: RawEntryBlock) -> UnifiedGraphBundle:
        parsed = parse_pharmacopoeia_entry(block)
        extraction = _build_rule_based_extraction(parsed)
        return build_pharmacopoeia_bundle(block, parsed, extraction)


def _build_rule_based_extraction(parsed) -> PharmacopoeiaExtractionResult:
    pinyin_name = parsed.header_lines[0] if parsed.header_lines else None
    latin_name = parsed.header_lines[1] if len(parsed.header_lines) > 1 else None
    piece_sections = parsed.piece_sections

    flavor_text = piece_sections.get("性味与归经", "")
    flavors, nature = normalize_flavors_and_nature(flavor_text)
    meridians = normalize_meridians(flavor_text) if "归" in flavor_text else []
    efficacy_text = piece_sections.get("功能与主治", "")
    efficacies = [item.strip() for item in efficacy_text.split("，")[:2] if item.strip()]
    prepared_piece = None
    if piece_sections:
        prepared_piece = PharmacopoeiaPreparedPieceExtraction(
            piece_name=f"{parsed.title_zh}饮片",
            parent_herb_name=parsed.title_zh,
            processing_text=piece_sections.get("炮制"),
            flavors=flavors,
            nature=nature,
            meridians=meridians,
            efficacies=efficacies,
        )
    return PharmacopoeiaExtractionResult(
        herb=PharmacopoeiaHerbExtraction(
            herb_name=parsed.title_zh,
            pinyin_name=pinyin_name,
            latin_name=latin_name,
        ),
        prepared_piece=prepared_piece,
    )


class PipelineProcessorRuntime:
    def __init__(self, extraction_client: PipelineStructuredExtractionClient | None = None) -> None:
        self.registry = ProcessorRegistry()
        self.extraction_client = extraction_client
        self.registry.register(PHARMACOPOEIA_2022_ROUTE_KEY, Pharmacopoeia2022Processor())

    def build_file_context(self, *, provider: str, dataset: str, file_path: str, local_abspath: str) -> SourceFileContext:
        path = Path(local_abspath)
        line_count = path.read_text(encoding="utf-8").count("\n") + 1
        return SourceFileContext(
            provider=provider,
            dataset=dataset,
            file_path=file_path,
            local_abspath=str(path),
            file_size=path.stat().st_size,
            line_count=line_count,
        )

    def resolve_processor(self, context: SourceFileContext) -> Any:
        return self.registry.resolve(
            provider=context.provider,
            dataset=context.dataset,
            file_path=context.file_path,
        )

    async def process_materialized_source(self, *, run: PipelineRun, materialized_source: MaterializedSource) -> UnifiedGraphBundle | None:
        candidate = self._select_candidate(run, materialized_source)
        if candidate is None:
            return None
        context = self.build_file_context(
            provider="huggingface",
            dataset=DATASET_NAME,
            file_path=PHARMACOPOEIA_2022_FILE_PATH,
            local_abspath=candidate,
        )
        processor = self.resolve_processor(context)
        blocks = processor.segment(context)
        if not blocks:
            return None
        return processor.process_entry(blocks[0])

    def _select_candidate(self, run: PipelineRun, materialized_source: MaterializedSource) -> str | None:
        desired = str(run.source_payload.get("file_path") or PHARMACOPOEIA_2022_FILE_PATH)
        for candidate in materialized_source.candidate_files:
            if candidate.endswith(desired) or candidate.endswith(Path(desired).name):
                return candidate
        return materialized_source.candidate_files[0] if materialized_source.candidate_files else None


def build_processor_runtime() -> PipelineProcessorRuntime:
    _ = PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT
    return PipelineProcessorRuntime(extraction_client=PipelineStructuredExtractionClient())
