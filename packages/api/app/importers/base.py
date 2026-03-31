"""
数据导入器基类
SSOT 数据模型的核心抽象层，支持 CSV/JSONL/HuggingFace 等多种数据源
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable

from knowledge_model.constants import EdgeType, parse_node_type
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord


EdgeRecord = GraphImportEdge
GraphRecord = GraphImportRecord

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
                parse_node_type(getattr(record.node_type, "value", record.node_type))
            except ValueError:
                errors.append(
                    f"invalid node_type: {getattr(record.node_type, 'value', record.node_type)}"
                )
        # 验证 edge types
        for edge in record.edges:
            try:
                EdgeType(getattr(edge.type, "value", edge.type))
            except ValueError:
                errors.append(f"invalid edge type: {getattr(edge.type, 'value', edge.type)}")
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
