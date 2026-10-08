"""JSONL 数据导入器"""

import json
from pathlib import Path
from typing import Iterable

from .base import AbstractDataImporter, EdgeRecord, GraphRecord, ImportStats
from graph_schema.constants import EdgeType, NodeStatus, parse_node_type


class JSONLImporter(AbstractDataImporter):
    """
    JSONL 导入器

    JSONL 格式（每行一个 JSON 对象）：
    {"node_type": "药材", "node_name": "陈皮", "source": "本草纲目", "herb_type": "base", "category": "理气药", "edges": [{"type": "包含成分", "target": "挥发油", "properties": {"quantity": "2-3%"}}]}
    {"node_type": "成分", "node_name": "挥发油", "source": "本草纲目", "edges": []}
    """

    def __init__(self):
        self._stats = ImportStats()

    def load(self, source: str) -> Iterable[GraphRecord]:
        """从 JSONL 文件加载记录"""
        self._stats = ImportStats()
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"JSONL file not found: {source}")

        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                self._stats.total += 1
                try:
                    data = json.loads(line)
                    record = self._parse_obj(data)
                    yield record
                except Exception as e:
                    self._stats.failed += 1
                    self._stats.errors.append(f"Line {line_num}: {e}")

    def _parse_obj(self, obj: dict) -> GraphRecord:
        """解析 JSON 对象"""
        # 解析 node_type
        node_type_str = obj.get("node_type")
        node_type = parse_node_type(node_type_str) if node_type_str else None

        # 解析边
        edges = []
        for edge_data in obj.get("edges", []):
            edge_type_str = edge_data.get("type", "")
            target = edge_data.get("target", "")
            if edge_type_str and target:
                edges.append(
                    EdgeRecord(
                        type=EdgeType(edge_type_str),
                        target=target,
                        properties=edge_data.get("properties", {}),
                    )
                )

        return GraphRecord(
            node_type=node_type,
            node_name=obj.get("node_name", ""),
            properties=obj.get("properties", {}),
            edges=edges,
            source=obj.get("source", ""),
            status=NodeStatus.PENDING,
        )

    def stats(self) -> ImportStats:
        return self._stats
