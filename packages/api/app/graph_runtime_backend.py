from typing import Any

from .kg.graph_metadata_service import graph_metadata_service
from .kg.graph_service import graph_service


class ApiGraphRuntimeBackend:
    async def search_nodes(
        self, query: str, label: str | None = None, limit: int = 20
    ) -> list[dict]:
        results = await graph_service.search_nodes(query, label=label, limit=limit)
        return [self._normalize_search_result(result) for result in results]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20) -> dict[str, Any]:
        return await graph_service.expand_node_graph(node_id, depth=depth, limit=limit)

    async def search_edges(
        self,
        rel_query: str,
        source_label: str | None = None,
        target_label: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        source_filter = f":{source_label}" if source_label else ""
        target_filter = f":{target_label}" if target_label else ""
        rows = await graph_service.execute_readonly_cypher(
            (
                f"MATCH (source{source_filter})-[r]->(target{target_filter}) "
                "WHERE type(r) CONTAINS $rel_query "
                "RETURN "
                "source {.id, .name, labels: labels(source)} AS source, "
                "target {.id, .name, labels: labels(target)} AS target, "
                "type(r) AS rel_type, properties(r) AS properties "
                "LIMIT $limit"
            ),
            {"rel_query": rel_query, "limit": limit},
        )
        return [dict(row) for row in rows]

    async def lookup_nodes(self, node_ids: list[str]) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for node_id in node_ids:
            node = await graph_service.get_node(node_id)
            if isinstance(node, dict):
                nodes.append(node)
        return nodes

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        return await graph_service.get_node(node_id)

    async def find_path(self, from_name: str, to_name: str, max_depth: int = 4) -> list[dict]:
        return await graph_service.find_path(from_name, to_name, max_depth=max_depth)

    async def execute_readonly_cypher(self, query: str) -> list[dict[str, Any]]:
        return await graph_service.execute_readonly_cypher(query)

    async def get_schema_summary(self) -> dict[str, Any]:
        return await graph_metadata_service.get_summary()

    def _normalize_search_result(self, result: dict[str, Any]) -> dict[str, Any]:
        node = result.get("node")
        if isinstance(node, dict):
            normalized = dict(node)
            if "labels" in result and "labels" not in normalized:
                normalized["labels"] = result["labels"]
            return normalized
        return result
