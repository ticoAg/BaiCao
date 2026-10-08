"""
数据导出器基类
支持 CSV/JSONL/HuggingFace Dataset 等多种导出格式
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from graph_schema.import_records import GraphImportRecord


@dataclass
class ExportStats:
    """导出统计"""
    total: int = 0
    success: int = 0
    failed: int = 0


class AbstractDataExporter(ABC):
    """抽象数据导出器"""

    @abstractmethod
    def export(self, records: list[GraphImportRecord], destination: str) -> ExportStats:
        """导出记录到目标"""
        ...

    @abstractmethod
    def stats(self) -> ExportStats:
        """返回导出统计"""
        ...
