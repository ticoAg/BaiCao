from __future__ import annotations

from pydantic_ai import Tool

from ..knowledge_mcp.handlers import KnowledgeMcpHandlers
from ..knowledge_mcp.payloads import wrap_edge_items, wrap_expand_subgraph, wrap_node_items


def build_graph_agent_tools(
    handlers: KnowledgeMcpHandlers | None = None,
) -> list[Tool]:
    graph = handlers or KnowledgeMcpHandlers()

    async def search_nodes(query: str, label: str | None = None, limit: int = 10) -> dict:
        """按名称模糊或按标识精确查询节点，用来定位锚点。"""
        return wrap_node_items(
            await graph.search_nodes({"query": query, "label": label, "limit": limit})
        )

    async def search_edges(
        rel_query: str,
        source_label: str | None = None,
        target_label: str | None = None,
        limit: int = 10,
    ) -> dict:
        """按中文关系名查询边。已知关系类型、尚未锁定锚点时使用。"""
        return wrap_edge_items(
            await graph.search_edges(
                {
                    "rel_query": rel_query,
                    "source_label": source_label,
                    "target_label": target_label,
                    "limit": limit,
                }
            )
        )

    async def expand_neighbors(node_id: str, depth: int = 1, limit: int = 20) -> dict:
        """围绕已定位锚点展开邻居。node_id 必须是节点「标识」。"""
        return wrap_expand_subgraph(
            await graph.expand_neighbors({"node_id": node_id, "depth": depth, "limit": limit})
        )

    async def lookup_nodes(node_ids: list[str]) -> dict:
        """按节点「标识」精确读取详情。"""
        return wrap_node_items(await graph.lookup_nodes({"node_ids": node_ids}))

    return [
        Tool(search_nodes, takes_ctx=False),
        Tool(search_edges, takes_ctx=False),
        Tool(expand_neighbors, takes_ctx=False),
        Tool(lookup_nodes, takes_ctx=False),
    ]
