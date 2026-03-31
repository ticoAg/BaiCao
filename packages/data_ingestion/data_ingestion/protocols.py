from typing import Protocol

from .bundles import UnifiedGraphBundle
from .source_models import RawEntryBlock, SourceFileContext


class FileProcessor(Protocol):
    route_key: "FileRouteKey"

    def segment(self, context: SourceFileContext) -> list[RawEntryBlock]:
        raise NotImplementedError

    def process_entry(self, block: RawEntryBlock) -> UnifiedGraphBundle:
        raise NotImplementedError
