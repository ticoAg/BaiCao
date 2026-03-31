from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FileRouteKey:
    provider: str
    dataset: str
    file_path: str


class ProcessorRegistry:
    def __init__(self) -> None:
        self._entries: list[tuple[FileRouteKey, Any]] = []

    def register(self, route_key: FileRouteKey, processor: Any) -> None:
        self._entries.append((route_key, processor))

    def resolve(self, *, provider: str, dataset: str, file_path: str) -> Any:
        for route_key, processor in self._entries:
            if (
                route_key.provider == provider
                and route_key.dataset == dataset
                and route_key.file_path == file_path
            ):
                return processor
        raise KeyError(f"No processor registered for {provider}/{dataset}/{file_path}")
