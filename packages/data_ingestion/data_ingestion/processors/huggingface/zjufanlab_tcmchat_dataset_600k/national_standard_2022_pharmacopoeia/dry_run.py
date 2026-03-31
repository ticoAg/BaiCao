from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from data_ingestion.source_models import SourceFileContext

from ..shared import DATASET_NAME, PHARMACOPOEIA_2022_FILE_PATH
from .llm_extraction import ExtractionTransport, extract_entry_with_llm
from .mapping import build_pharmacopoeia_bundle, edge_type_to_label
from .parsing import parse_pharmacopoeia_entry
from .prompts import build_pharmacopoeia_user_payload
from .segmentation import segment_pharmacopoeia_entries


class DryRunResult(BaseModel):
    output_dir: Path = Field(description="输出目录")
    summary: dict[str, object] = Field(description="运行摘要")

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=False)


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )


def _entry_key(block) -> str:
    return f"{block.entry_title}:{block.start_line}-{block.end_line}"


def run_pharmacopoeia_dry_run(
    *,
    local_path: Path,
    output_dir: Path,
    limit: int,
    entry_offset: int = 0,
    request_timeout_seconds: float | None = None,
    concurrency: int = 1,
    transport: ExtractionTransport,
    provider: str = "huggingface",
    dataset: str = DATASET_NAME,
    file_path: str = PHARMACOPOEIA_2022_FILE_PATH,
    on_entry_result: Callable[[dict[str, Any]], None] | None = None,
) -> DryRunResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    context = SourceFileContext(
        provider=provider,
        dataset=dataset,
        file_path=file_path,
        local_abspath=str(local_path),
        file_size=local_path.stat().st_size,
        line_count=local_path.read_text(encoding="utf-8").count("\n") + 1,
    )
    blocks = segment_pharmacopoeia_entries(context)[entry_offset : entry_offset + limit]
    parsed_sections = [parse_pharmacopoeia_entry(block) for block in blocks]
    async def _run_extractions():
        semaphore = asyncio.Semaphore(max(1, concurrency))
        results = [None] * len(blocks)

        async def _run_one(index: int, block, section):
            async with semaphore:
                result = await extract_entry_with_llm(
                    section,
                    transport,
                    request_timeout_seconds=request_timeout_seconds,
                )
            results[index] = result
            if on_entry_result is not None:
                on_entry_result(
                    {
                        "entry_key": _entry_key(block),
                        "entry_title": block.entry_title,
                        "status": result.status,
                        "elapsed_ms": result.elapsed_ms,
                        "raw_response_preview": result.raw_response_preview,
                        "error_message": result.error_message,
                    }
                )

        await asyncio.gather(
            *[_run_one(index, block, section) for index, (block, section) in enumerate(zip(blocks, parsed_sections, strict=False))]
        )
        return results

    llm_results = asyncio.run(_run_extractions())
    bundle_records: list[tuple[Any, Any]] = []
    for block, section, result in zip(blocks, parsed_sections, llm_results, strict=False):
        if result.validated_extraction is None:
            continue
        bundle_records.append((block, build_pharmacopoeia_bundle(block, section, result.validated_extraction)))

    _write_jsonl(output_dir / "entries.jsonl", [block.model_dump(mode="json") for block in blocks])
    _write_jsonl(output_dir / "parsed_sections.jsonl", [section.model_dump(mode="json") for section in parsed_sections])
    _write_jsonl(
        output_dir / "llm_requests.jsonl",
        [
            {
                "entry_key": _entry_key(block),
                "entry_title": block.entry_title,
                "payload": build_pharmacopoeia_user_payload(section),
            }
            for block, section in zip(blocks, parsed_sections, strict=False)
        ],
    )
    _write_jsonl(
        output_dir / "llm_responses.jsonl",
        [
            {
                "entry_key": _entry_key(block),
                "entry_title": block.entry_title,
                "raw_response": result.raw_response,
                "raw_response_preview": result.raw_response_preview,
                "elapsed_ms": result.elapsed_ms,
            }
            for block, result in zip(blocks, llm_results, strict=False)
        ],
    )
    _write_jsonl(
        output_dir / "validated_extractions.jsonl",
        [
            {
                "entry_key": _entry_key(block),
                "entry_title": block.entry_title,
                "status": result.status,
                "elapsed_ms": result.elapsed_ms,
                "raw_response_preview": result.raw_response_preview,
                "error_message": result.error_message,
                "validated_extraction": (
                    result.validated_extraction.model_dump(mode="json") if result.validated_extraction else None
                ),
            }
            for block, result in zip(blocks, llm_results, strict=False)
        ],
    )
    _write_jsonl(
        output_dir / "graph_bundles.jsonl",
        [
            {
                "entry_key": _entry_key(block),
                "entry_title": block.entry_title,
                "node_count": len(bundle.nodes),
                "edge_count": len(bundle.edges),
                "node_names": [node.name for node in bundle.nodes],
                "edge_types": [edge_type_to_label(edge.type) for edge in bundle.edges],
                "record_count": len(bundle.records),
                "bundle_errors": bundle.errors,
            }
            for block, bundle in bundle_records
        ],
    )

    summary = {
        "entries_attempted": len(blocks),
        "entries_succeeded": sum(1 for result in llm_results if result.status == "success"),
        "entries_failed": sum(1 for result in llm_results if result.status != "success"),
        "llm_json_invalid_count": sum(1 for result in llm_results if result.status == "llm_json_invalid"),
        "llm_request_failed_count": sum(1 for result in llm_results if result.status == "llm_request_failed"),
        "llm_schema_invalid_count": sum(1 for result in llm_results if result.status == "llm_schema_invalid"),
        "mapping_success_count": len(bundle_records),
        "total_llm_elapsed_ms": sum(result.elapsed_ms for result in llm_results),
        "generated_at": datetime.now().isoformat(),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "run_config.json").write_text(
        json.dumps(
            {
                "provider": provider,
                "dataset": dataset,
                "file_path": file_path,
                "local_path": str(local_path),
                "limit": limit,
                "entry_offset": entry_offset,
                "request_timeout_seconds": request_timeout_seconds,
                "concurrency": concurrency,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text("# pharmacopoeia dry-run\n", encoding="utf-8")

    return DryRunResult(output_dir=output_dir, summary=summary)
