"""BaiCao 知识图谱 MCP server。

实现官方 Python MCP SDK（stdio + Streamable HTTP）。
Streamable HTTP 是现行 MCP 传输（取代 HTTP+SSE）。
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from .handlers import KnowledgeMcpHandlers

KNOWLEDGE_MCP_INSTRUCTIONS = (
    "白草中医药知识图谱工具。节点/关系/属性键一律中文。"
    "先 search_nodes 定位，再 expand_neighbors 或 search_edges。"
    "read_cypher 只用中文键：名称、标识、导入源。不要写 id/name。"
)

_handlers = KnowledgeMcpHandlers()


def _dump(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, default=str)


def create_knowledge_mcp() -> FastMCP:
    mcp = FastMCP(
        "baicao-knowledge",
        instructions=KNOWLEDGE_MCP_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
    )

    @mcp.tool()
    async def search_nodes(query: str, label: str | None = None, limit: int = 5) -> str:
        """按关键词模糊查询图谱节点。标签用中文：药材/方剂/医案/穴位/治法。"""
        return _dump(await _handlers.search_nodes({"query": query, "label": label, "limit": limit}))

    @mcp.tool()
    async def search_edges(
        rel_query: str,
        source_label: str | None = None,
        target_label: str | None = None,
        limit: int = 10,
    ) -> str:
        """按关系关键词查询边。关系名用中文，如 组成药材、使用方剂。"""
        return _dump(
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
    async def expand_neighbors(node_id: str, depth: int = 1, limit: int = 20) -> str:
        """围绕已定位节点做邻居展开。node_id 用节点标识。"""
        return _dump(
            await _handlers.expand_neighbors({"node_id": node_id, "depth": depth, "limit": limit})
        )

    @mcp.tool()
    async def lookup_nodes(node_ids: list[str]) -> str:
        """按节点标识精确读取详情。"""
        return _dump(await _handlers.lookup_nodes({"node_ids": node_ids}))

    @mcp.tool()
    async def read_cypher(query: str) -> str:
        """只读 Cypher。属性键用 名称/标识，不要写 n.id / n.name。"""
        return _dump(await _handlers.read_cypher({"query": query}))

    return mcp


knowledge_mcp = create_knowledge_mcp()
