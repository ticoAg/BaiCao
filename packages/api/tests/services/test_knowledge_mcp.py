from unittest.mock import AsyncMock

import pytest

from app.services.graph_tools.read_cypher import build_read_cypher_tool
from app.services.knowledge_mcp.handlers import KnowledgeMcpHandlers, reject_write_cypher
from app.services.knowledge_mcp.server import create_knowledge_mcp


def test_reject_write_cypher():
    assert reject_write_cypher("MATCH (n:方剂) RETURN n.名称") is None
    assert reject_write_cypher("CREATE (n:药材 {名称:'x'})") is not None
    assert reject_write_cypher("MATCH (n) SET n.状态 = '已验证'") is not None


@pytest.mark.asyncio
async def test_search_nodes_handler_forwards_to_backend():
    backend = AsyncMock()
    backend.search_nodes = AsyncMock(return_value=[{"id": "formula-乌梅丸", "name": "乌梅丸"}])
    handlers = KnowledgeMcpHandlers(backend_factory=lambda: backend)

    result = await handlers.search_nodes({"query": "乌梅丸", "label": "方剂", "limit": 3})

    backend.search_nodes.assert_awaited_once_with(query="乌梅丸", label="方剂", limit=3)
    assert result[0]["name"] == "乌梅丸"


@pytest.mark.asyncio
async def test_knowledge_mcp_lists_graph_tools():
    mcp = create_knowledge_mcp()
    tools = await mcp.list_tools()
    assert {tool.name for tool in tools} == {
        "search_nodes",
        "search_edges",
        "expand_neighbors",
        "lookup_nodes",
        "read_cypher",
    }


@pytest.mark.asyncio
async def test_read_cypher_tool_uses_mcp_write_guard():
    tool = build_read_cypher_tool()
    result = await tool.ainvoke({"query": "CREATE (n:药材 {名称:'x'})"})
    assert "只允许只读" in result["error"]
