"""CSV 数据导出器"""

import csv
import json
from pathlib import Path

from .base import AbstractDataExporter, ExportStats
from graph_schema.import_records import GraphImportEdge, GraphImportRecord


class CSVExporter(AbstractDataExporter):
    """CSV 导出器"""

    def __init__(self):
        self._stats = ExportStats()

    def export(self, records: list[GraphImportRecord], destination: str) -> ExportStats:
        self._stats = ExportStats(total=len(records))
        path = Path(destination)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "node_type", "node_name", "source", "herb_type", "category",
                    "description", "edge_type", "target", "edge_properties",
                ],
            )
            writer.writeheader()

            for record in records:
                try:
                    row = self._record_to_row(record)
                    writer.writerow(row)
                    self._stats.success += 1
                except Exception:
                    self._stats.failed += 1

        return self._stats

    def _record_to_row(self, record: GraphImportRecord) -> dict:
        """将 GraphRecord 转换为 CSV 行"""
        props = record.properties or {}

        # 提取第一个边的信息（CSV 格式限制每行一个边）
        edge_type = ""
        edge_target = ""
        edge_props = "{}"

        if record.edges:
            first_edge: GraphImportEdge = record.edges[0]
            edge_type = first_edge.type.value
            edge_target = first_edge.target
            edge_props = json.dumps(first_edge.properties or {}, ensure_ascii=False)

        return {
            "node_type": record.node_type.value if record.node_type else "",
            "node_name": record.node_name,
            "source": record.source,
            "herb_type": props.get("herb_type", ""),
            "category": props.get("category", ""),
            "description": props.get("description", ""),
            "edge_type": edge_type,
            "target": edge_target,
            "edge_properties": edge_props,
        }

    def stats(self) -> ExportStats:
        return self._stats
