from unittest.mock import AsyncMock, patch

import pytest

from app.graph_runtime_backend import ApiGraphRuntimeBackend
from app.services.graph_tools.registry import build_graph_tools


def test_build_graph_tools_registers_only_foundational_graph_tools():
    tools = build_graph_tools()
    names = [tool.name for tool in tools]

    assert names == [
        "search_nodes",
        "search_edges",
        "expand_neighbors",
        "lookup_nodes",
        "read_cypher",
    ]
    assert "graph_cypher_qa" not in names


def test_search_nodes_tool_description_guides_agent_to_anchor_first():
    tools = build_graph_tools()
    tool = next(tool for tool in tools if tool.name == "search_nodes")

    assert "锚点" in tool.description
    assert "模糊" in tool.description


@pytest.mark.asyncio
async def test_search_edges_projects_chinese_identity_keys():
    backend = ApiGraphRuntimeBackend()
    backend.execute_readonly_cypher = AsyncMock(return_value=[])  # type: ignore[method-assign]
    with patch("app.graph_runtime_backend.graph_service") as mock_svc:
        mock_svc.execute_readonly_cypher = AsyncMock(return_value=[])
        await backend.search_edges(rel_query="组成药材", source_label="方剂", limit=5)
        assert mock_svc.execute_readonly_cypher.await_args is not None
        query = mock_svc.execute_readonly_cypher.await_args.args[0]
    assert "source.标识" in query
    assert "source.名称" in query
    assert "source {.id, .name" not in query
