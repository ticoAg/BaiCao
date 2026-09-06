from typing import Any

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
                "source {id: source.标识, name: source.名称, labels: labels(source)} AS source, "
                "target {id: target.标识, name: target.名称, labels: labels(target)} AS target, "
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

    def _normalize_search_result(self, result: dict[str, Any]) -> dict[str, Any]:
        node = result.get("node")
        if isinstance(node, dict):
            normalized = dict(node)
            if "labels" in result and "labels" not in normalized:
                normalized["labels"] = result["labels"]
            return normalized
        return result
