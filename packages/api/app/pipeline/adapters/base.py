from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class SourceDescriptor:
    adapter: str
    source_type: str
    locator: str
    source_summary: dict[str, Any]
    raw_text: str = ""
    sample_lines: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class SourceAdapter(Protocol):
    source_type: str

    def describe(self, source_locator: str) -> SourceDescriptor: ...


def resolve_local_path(source_locator: str) -> Path:
    locator_path = Path(source_locator).expanduser()
    if locator_path.is_absolute():
        return locator_path

    cwd_path = Path.cwd() / locator_path
    if cwd_path.exists():
        return cwd_path

    repo_root = Path(__file__).resolve().parents[5]
    return repo_root / locator_path


def describe_local_text_file(
    source_type: str,
    source_locator: str,
    *,
    format_name: str,
    max_lines: int = 3,
) -> SourceDescriptor:
    path = resolve_local_path(source_locator)
    if not path.exists():
        return SourceDescriptor(
            adapter=source_type,
            source_type=source_type,
            locator=source_locator,
            source_summary={
                "kind": "file",
                "format": format_name,
                "exists": False,
                "path": str(path),
            },
            errors=[f"来源文件不存在: {source_locator}"],
        )

    lines = path.read_text(encoding="utf-8").splitlines()
    sample_lines = [line for line in lines[:max_lines]]
    metadata: dict[str, Any] = {
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "line_count": len(lines),
    }

    if format_name == "jsonl":
        records = []
        for line in sample_lines:
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        metadata["preview_records"] = records
    elif format_name == "csv" and len(sample_lines) >= 2:
        try:
            metadata["preview_records"] = list(csv.DictReader(sample_lines))
        except csv.Error:
            metadata["preview_records"] = []

    return SourceDescriptor(
        adapter=source_type,
        source_type=source_type,
        locator=source_locator,
        source_summary={
            "kind": "file",
            "format": format_name,
            "exists": True,
            "path": str(path),
            "sample_lines": sample_lines,
            "line_count": len(lines),
        },
        sample_lines=sample_lines,
        metadata=metadata,
    )


class FallbackSourceAdapter:
    source_type = "fallback"

    def __init__(self, requested_source_type: str) -> None:
        self.requested_source_type = requested_source_type

    def describe(self, source_locator: str) -> SourceDescriptor:
        return SourceDescriptor(
            adapter=self.requested_source_type,
            source_type=self.requested_source_type,
            locator=source_locator,
            source_summary={
                "kind": "opaque_locator",
                "source_type": self.requested_source_type,
                "locator": source_locator,
                "is_valid": bool(source_locator.strip()),
            },
            raw_text=source_locator.strip(),
            warnings=[f"暂未提供 {self.requested_source_type} 专用预览，已回退为 locator 摘要"],
            errors=[] if source_locator.strip() else ["来源 locator 不能为空"],
        )
