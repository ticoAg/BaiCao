"""提供药典条目抽取链路的离线 dry-run 入口。"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field

from ..shared import DATASET_NAME, PHARMACOPOEIA_2022_FILE_PATH
from .ingestion import run_pharmacopoeia_ingestion
from .llm_extraction import ExtractionTransport


class DryRunResult(BaseModel):
    """封装一次 dry-run 的输出目录和摘要结果。"""

    output_dir: Path = Field(description="输出目录")
    summary: dict[str, object] = Field(description="运行摘要")

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=False)

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
    """串联切段、解析、LLM 抽取、映射与调试产物落盘。"""
    result = run_pharmacopoeia_ingestion(
        local_path=local_path,
        output_dir=output_dir,
        limit=limit,
        entry_offset=entry_offset,
        request_timeout_seconds=request_timeout_seconds,
        concurrency=concurrency,
        transport=transport,
        provider=provider,
        dataset=dataset,
        file_path=file_path,
        on_entry_result=on_entry_result,
    )
    return DryRunResult(output_dir=result.output_dir, summary=result.summary)
