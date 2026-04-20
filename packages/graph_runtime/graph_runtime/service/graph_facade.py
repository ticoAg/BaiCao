from .backend import GraphRuntimeBackend
from .cypher_readonly import ensure_readonly_cypher


class GraphFacade:
    def __init__(self, backend: GraphRuntimeBackend) -> None:
        self.backend = backend

    async def search_nodes(
        self, query: str, label: str | None = None, limit: int = 20
    ) -> list[dict]:
        return await self.backend.search_nodes(query=query, label=label, limit=limit)

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20) -> dict:
        return await self.backend.expand_neighbors(node_id=node_id, depth=depth, limit=limit)

    async def read_cypher(self, query: str) -> list[dict]:
        normalized = ensure_readonly_cypher(query)
        return await self.backend.execute_readonly_cypher(normalized)
