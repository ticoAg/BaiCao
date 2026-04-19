"""提供数据来源文件到专属处理器的路由注册能力。"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FileRouteKey:
    """唯一标识一个来源文件处理器的路由键。"""

    provider: str
    dataset: str
    file_path: str


class ProcessorRegistry:
    """维护来源文件与处理器实例之间的精确匹配关系。"""

    def __init__(self) -> None:
        """初始化一个空的处理器注册表。"""

        self._entries: list[tuple[FileRouteKey, Any]] = []

    def register(self, route_key: FileRouteKey, processor: Any) -> None:
        """注册某个来源文件对应的处理器实现。"""

        self._entries.append((route_key, processor))

    def resolve(self, *, provider: str, dataset: str, file_path: str) -> Any:
        """按 provider、dataset 和 file_path 精确解析处理器。"""

        for route_key, processor in self._entries:
            if (
                route_key.provider == provider
                and route_key.dataset == dataset
                and route_key.file_path == file_path
            ):
                return processor
        raise KeyError(f"No processor registered for {provider}/{dataset}/{file_path}")
