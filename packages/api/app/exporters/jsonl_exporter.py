"""JSONL 数据导出器"""

import json
from pathlib import Path

from .base import AbstractDataExporter, ExportStats
from ..importers.base import GraphRecord


class JSONLExporter(AbstractDataExporter):
    """JSONL 导出器"""

    def __init__(self):
        self._stats = ExportStats()

    def export(self, records: list[GraphRecord], destination: str) -> ExportStats:
        self._stats = ExportStats(total=len(records))
        path = Path(destination)

        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                try:
                    line = json.dumps(record.to_dict(), ensure_ascii=False)
                    f.write(line + "\n")
                    self._stats.success += 1
                except Exception:
                    self._stats.failed += 1

        return self._stats

    def stats(self) -> ExportStats:
        return self._stats
