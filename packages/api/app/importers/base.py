"""
数据导入器基类
SSOT 数据模型的核心抽象层，支持 CSV/JSONL/HuggingFace 等多种数据源
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable, Any

from ..models.enums import EdgeType, NodeStatus, NodeType


@dataclass
class EdgeRecord:
    """边记录"""
    type: EdgeType
    target: str
    properties: dict | None = None


@dataclass
class GraphRecord:
    """图谱记录 - 导入/导出的最小单位"""
    node_type: NodeType | None = None
    node_name: str = ""
    properties: dict = field(default_factory=dict)
    edges: list[EdgeRecord] = field(default_factory=list)
    source: str = ""
    status: NodeStatus = NodeStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "node_type": self.node_type.value if self.node_type else None,
            "node_name": self.node_name,
            "properties": self.properties,
            "edges": [
                {
                    "type": e.type.value,
                    "target": e.target,
                    "properties": e.properties or {},
                }
                for e in self.edges
            ],
            "source": self.source,
            "status": self.status.value,
        }


@dataclass
class ImportStats:
    """导入统计"""
    total: int = 0
    success: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.success / self.total


@dataclass
class ImportResult:
    """导入结果"""
    stats: ImportStats
    records: list[GraphRecord] = field(default_factory=list)


class AbstractDataImporter(ABC):
    """
    抽象数据导入器
    所有导入器必须实现 load() 和 validate() 方法
    """

    @abstractmethod
    def load(self, source: str) -> Iterable[GraphRecord]:
        """从数据源加载记录"""
        ...

    def validate(self, record: GraphRecord) -> list[str]:
        """验证单条记录，返回错误列表，空列表表示通过"""
        errors = []
        if not record.node_name:
            errors.append("node_name is required")
        if record.node_type is None:
            errors.append("node_type is required")
        if not record.source:
            errors.append("source is required")
        # 验证 node_type 合法性
        if record.node_type is not None:
            try:
                NodeType(record.node_type.value)
            except ValueError:
                errors.append(f"invalid node_type: {record.node_type.value}")
        # 验证 edge types
        for edge in record.edges:
            try:
                EdgeType(edge.type.value)
            except ValueError:
                errors.append(f"invalid edge type: {edge.type.value}")
        return errors

    @abstractmethod
    def stats(self) -> ImportStats:
        """返回导入统计"""
        ...

    def import_all(self, source: str, dry_run: bool = False) -> ImportResult:
        """
        执行完整导入流程
        1. load() 加载所有记录
        2. validate() 验证每条记录
        3. 返回统计信息
        """
        stats = ImportStats()
        records = []

        for record in self.load(source):
            stats.total += 1
            errors = self.validate(record)

            if errors:
                stats.failed += 1
                stats.errors.extend([f"Row {stats.total}: {e}" for e in errors])
            else:
                stats.success += 1
                records.append(record)

        return ImportResult(stats=stats, records=records)
