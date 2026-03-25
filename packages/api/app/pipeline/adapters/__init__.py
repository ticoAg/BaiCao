from .base import FallbackSourceAdapter, SourceAdapter, SourceDescriptor
from .csv import CSVSourceAdapter
from .huggingface import HuggingFaceSourceAdapter
from .jsonl import JSONLSourceAdapter
from .manual import ManualSourceAdapter


def build_source_adapters() -> dict[str, SourceAdapter]:
    return {
        "manual": ManualSourceAdapter(),
        "jsonl": JSONLSourceAdapter(),
        "csv": CSVSourceAdapter(),
        "huggingface": HuggingFaceSourceAdapter(),
    }


def get_source_adapter(source_type: str, adapters: dict[str, SourceAdapter]) -> SourceAdapter:
    return adapters.get(source_type, FallbackSourceAdapter(source_type))


__all__ = [
    "CSVSourceAdapter",
    "FallbackSourceAdapter",
    "HuggingFaceSourceAdapter",
    "JSONLSourceAdapter",
    "ManualSourceAdapter",
    "SourceAdapter",
    "SourceDescriptor",
    "build_source_adapters",
    "get_source_adapter",
]
