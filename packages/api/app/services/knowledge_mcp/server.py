"""BaiCao 知识图谱 MCP server。

实现官方 Python MCP SDK（stdio + Streamable HTTP）。
Streamable HTTP 是现行 MCP 传输（取代 HTTP+SSE）。
chat 主链不再当 MCP 客户端；本 server 给 Cursor / `/mcp` 外部调用。
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .handlers import KnowledgeMcpHandlers
from .payloads import wrap_edge_items, wrap_expand_subgraph, wrap_node_items
from .schema import build_graph_schema

KNOWLEDGE_MCP_INSTRUCTIONS = (
    "白草中医药知识图谱只读工具。先 search_nodes 定位锚点，再 expand_neighbors 或 search_edges；"
    "lookup_nodes 按「标识」回看属性。读 graph://schema 了解标签与关系。不要编写或执行 Cypher。"
)

_handlers = KnowledgeMcpHandlers()


def create_knowledge_mcp() -> FastMCP:
    mcp = FastMCP(
        "baicao-knowledge",
        instructions=KNOWLEDGE_MCP_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
    )

    @mcp.resource("graph://schema", mime_type="application/json")
    async def graph_schema() -> dict:
        """当前图的中文标签、关系类型，以及「标识」用法。"""
        return await build_graph_schema()

    @mcp.tool()
    async def search_nodes(query: str, label: str | None = None, limit: int = 10) -> dict:
        """按名称模糊或按标识精确查询节点，用来定位锚点。

        query: 中文名称关键词，或精确「标识」（如 formula-乌梅丸）。
        label: 可选中文类型，如 药材/方剂/医案/穴位/治法。
        limit: 候选上限，默认 10。
        """
        return wrap_node_items(
            await _handlers.search_nodes({"query": query, "label": label, "limit": limit})
        )

    @mcp.tool()
    async def search_edges(
        rel_query: str,
        source_label: str | None = None,
        target_label: str | None = None,
        limit: int = 10,
    ) -> dict:
        """按中文关系名查询边。已知关系类型、尚未锁定锚点时使用。

        rel_query: 如 组成药材、使用方剂、由证据支持、来源于。
        source_label / target_label: 可选中文节点类型。
        """
        return wrap_edge_items(
            await _handlers.search_edges(
                {
                    "rel_query": rel_query,
                    "source_label": source_label,
                    "target_label": target_label,
                    "limit": limit,
                }
            )
        )

    @mcp.tool()
    async def expand_neighbors(node_id: str, depth: int = 1, limit: int = 20) -> dict:
        """围绕已定位锚点展开邻居。node_id 必须是节点「标识」，不要传名称。

        depth: 1 或 2。证据「来源于」通常在第 2 跳。
        limit: 子图节点上限。
        """
        return wrap_expand_subgraph(
            await _handlers.expand_neighbors({"node_id": node_id, "depth": depth, "limit": limit})
        )

    @mcp.tool()
    async def lookup_nodes(node_ids: list[str]) -> dict:
        """按节点「标识」精确读取详情。已有候选后回看属性，不要再模糊搜索。"""
        return wrap_node_items(await _handlers.lookup_nodes({"node_ids": node_ids}))

    return mcp


knowledge_mcp = create_knowledge_mcp()
