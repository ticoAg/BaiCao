"""BaiCao 数据采集边界包的公共导出入口。"""

from .models import ExtractionCandidate, SourceDocument
from .async_batch import run_async_batch
from .bundles import UnifiedGraphBundle
from .record_snapshots import flatten_graph_import_records, write_graph_import_records_jsonl
from .routing import FileRouteKey, ProcessorRegistry
from .source_models import RawEntryBlock, SourceFileContext

# 对外统一暴露图谱前处理中最常用的模型和协议入口。
__all__ = [
    "ExtractionCandidate",
    "FileRouteKey",
    "ProcessorRegistry",
    "RawEntryBlock",
    "SourceDocument",
    "SourceFileContext",
    "UnifiedGraphBundle",
    "flatten_graph_import_records",
    "run_async_batch",
    "write_graph_import_records_jsonl",
]
