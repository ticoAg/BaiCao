"""CSV 数据导入器"""

import csv
import json
from pathlib import Path
from typing import Iterable

from .base import AbstractDataImporter, EdgeRecord, GraphRecord, ImportStats
from knowledge_model.constants import EdgeType, NodeStatus, NodeType


class CSVImporter(AbstractDataImporter):
    """
    CSV 导入器

    CSV 格式约定：
    node_type,node_name,source,herb_type,category,description,edge_type,target,edge_properties
    Herb,陈皮,本草纲目,base,理气药,芸香科...,,
    Component,挥发油,本草纲目,,,,CONTAINS,陈皮,"{""quantity"": ""2-3%""}"
    Variant,大红皮,本草纲目,,,,HAS_VARIANT,陈皮,
    Efficacy,理气,本草纲目,,,,HAS_EFFICACY,陈皮,

    edge_properties 为可选的 JSON 字符串
    """

    def __init__(self):
        self._stats = ImportStats()

    def load(self, source: str) -> Iterable[GraphRecord]:
        """从 CSV 文件加载记录"""
        self._stats = ImportStats()
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {source}")

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):  # start=2 因为第1行是表头
                self._stats.total += 1
                try:
                    record = self._parse_row(row)
                    yield record
                except Exception as e:
                    self._stats.failed += 1
                    self._stats.errors.append(f"Row {row_num}: {e}")

    def _parse_row(self, row: dict) -> GraphRecord:
        """解析 CSV 行"""
        # 解析 node_type
        node_type_str = row.get("node_type", "").strip()
        node_type = NodeType(node_type_str) if node_type_str else None

        # 解析边
        edges = []
        edge_type_str = row.get("edge_type", "").strip()
        target = row.get("target", "").strip()

        if edge_type_str and target:
            edge_props_str = row.get("edge_properties", "").strip()
            edge_props = {}
            if edge_props_str:
                try:
                    edge_props = json.loads(edge_props_str)
                except json.JSONDecodeError:
                    edge_props = {}
            edges.append(
                EdgeRecord(
                    type=EdgeType(edge_type_str),
                    target=target,
                    properties=edge_props,
                )
            )

        # 解析属性
        props = {}
        for key in ("herb_type", "category", "description", "chemical_formula",
                    "parent_herb", "min_duration", "conditions", "trait_category",
                    "years", "quality_indicator", "nature", "tcm_type"):
            if row.get(key):
                val = row[key].strip()
                if key == "years":
                    props[key] = int(val) if val.isdigit() else val
                else:
                    props[key] = val

        return GraphRecord(
            node_type=node_type,
            node_name=row.get("node_name", "").strip(),
            properties=props,
            edges=edges,
            source=row.get("source", "").strip(),
            status=NodeStatus.PENDING,
        )

    def stats(self) -> ImportStats:
        return self._stats
