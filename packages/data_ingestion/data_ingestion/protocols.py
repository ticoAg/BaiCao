"""声明来源文件处理器需要满足的最小协议。"""

from typing import Protocol

from .bundles import UnifiedGraphBundle
from .source_models import RawEntryBlock, SourceFileContext


class FileProcessor(Protocol):
    """约束文件级处理器应实现的切段和条目处理接口。"""

    route_key: "FileRouteKey"

    def segment(self, context: SourceFileContext) -> list[RawEntryBlock]:
        """把一个来源文件切成后续可解析的原始条目块。"""

        raise NotImplementedError

    def process_entry(self, block: RawEntryBlock) -> UnifiedGraphBundle:
        """把单个原始条目块处理为统一图谱 bundle。"""

        raise NotImplementedError
