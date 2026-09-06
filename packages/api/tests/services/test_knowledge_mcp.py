from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.services.graph_tools.read_cypher import build_read_cypher_tool
from app.services.knowledge_mcp.handlers import KnowledgeMcpHandlers, reject_write_cypher
from app.services.knowledge_mcp.payloads import wrap_expand_subgraph, wrap_node_items
from app.services.knowledge_mcp.schema import build_graph_schema
from app.services.knowledge_mcp.server import KNOWLEDGE_MCP_INSTRUCTIONS, create_knowledge_mcp


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
    by_name = {tool.name: tool for tool in tools}
    assert set(by_name) == {
        "search_nodes",
        "search_edges",
        "expand_neighbors",
        "lookup_nodes",
    }
    assert "read_cypher" not in by_name
    assert "标识" in (by_name["search_nodes"].description or "")
    assert "锚点" in (by_name["search_nodes"].description or "")
    assert "标识" in (by_name["expand_neighbors"].description or "")
    assert "2" in (by_name["expand_neighbors"].description or "")


@pytest.mark.asyncio
async def test_knowledge_mcp_exposes_schema_resource():
    mcp = create_knowledge_mcp()
    resources = await mcp.list_resources()
    uris = {str(resource.uri) for resource in resources}
    assert "graph://schema" in uris


def test_knowledge_mcp_instructions_omit_raw_cypher():
    assert "search_nodes" in KNOWLEDGE_MCP_INSTRUCTIONS
    assert "lookup_nodes" in KNOWLEDGE_MCP_INSTRUCTIONS
    assert "read_cypher" not in KNOWLEDGE_MCP_INSTRUCTIONS
    assert "不要编写或执行 Cypher" in KNOWLEDGE_MCP_INSTRUCTIONS


def test_wrap_node_items_empty_includes_hint():
    payload = wrap_node_items([])
    assert payload["count"] == 0
    assert payload["items"] == []
    assert "标识" in payload["hint"]


def test_wrap_expand_subgraph_missing_center_includes_hint():
    payload = wrap_expand_subgraph({"center": None, "nodes": [], "edges": []})
    assert payload["hint"]
    assert payload["node_count"] == 0


@pytest.mark.asyncio
async def test_build_graph_schema_falls_back_to_knowledge_model():
    with patch(
        "app.services.knowledge_mcp.schema.graph_metadata_service.list_labels",
        AsyncMock(side_effect=RuntimeError("no db")),
    ):
        schema = await build_graph_schema()
    assert schema["id_field"] == "标识"
    names = {item["name"] for item in schema["labels"]}
    assert "药材" in names
    assert "方剂" in names
    rels = {item["name"] for item in schema["relationship_types"]}
    assert "组成药材" in rels
    assert "由证据支持" in rels


@pytest.mark.asyncio
async def test_read_cypher_tool_uses_mcp_write_guard():
    tool = build_read_cypher_tool()
    payload: Any = {"query": "CREATE (n:药材 {名称:'x'})"}
    result = await tool.ainvoke(payload)
    assert "只允许只读" in result["error"]
