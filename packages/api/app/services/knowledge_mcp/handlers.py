from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ...graph_runtime_backend import ApiGraphRuntimeBackend


class KnowledgeMcpHandlers:
    def __init__(
        self,
        backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
    ) -> None:
        self._backend_factory = backend_factory or ApiGraphRuntimeBackend

    def _backend(self) -> ApiGraphRuntimeBackend:
        return self._backend_factory()

    async def search_nodes(self, args: dict[str, Any]) -> Any:
        return await self._backend().search_nodes(
            query=str(args.get("query") or ""),
            label=args.get("label"),
            limit=int(args.get("limit") or 10),
        )

    async def search_edges(self, args: dict[str, Any]) -> Any:
        return await self._backend().search_edges(
            rel_query=str(args.get("rel_query") or ""),
            source_label=args.get("source_label"),
            target_label=args.get("target_label"),
            limit=int(args.get("limit") or 10),
        )

    async def expand_neighbors(self, args: dict[str, Any]) -> Any:
        return await self._backend().expand_neighbors(
            node_id=str(args.get("node_id") or ""),
            depth=int(args.get("depth") or 1),
            limit=int(args.get("limit") or 20),
        )

    async def lookup_nodes(self, args: dict[str, Any]) -> Any:
        node_ids = args.get("node_ids") or []
        if isinstance(node_ids, str):
            node_ids = [node_ids]
        return await self._backend().lookup_nodes([str(item) for item in node_ids])
