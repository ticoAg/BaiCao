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
