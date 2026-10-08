"""提供 GraphImportRecord 快照的通用扁平化与落盘能力。"""

from __future__ import annotations

import json
from pathlib import Path

from graph_schema.import_records import GraphImportRecord

from .bundles import UnifiedGraphBundle


def flatten_graph_import_records(bundles: list[UnifiedGraphBundle]) -> list[GraphImportRecord]:
    """把多个 bundle 内的导入记录按原始顺序展开成单一列表。"""

    records: list[GraphImportRecord] = []
    for bundle in bundles:
        records.extend(
            record for record in bundle.records if isinstance(record, GraphImportRecord)
        )
    return records


def write_graph_import_records_jsonl(path: Path, records: list[GraphImportRecord]) -> None:
    """把共享导入记录快照写成 JSONL，供后续导入器或审查复用。"""

    path.write_text(
        "\n".join(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) for record in records)
        + "\n",
        encoding="utf-8",
    )
