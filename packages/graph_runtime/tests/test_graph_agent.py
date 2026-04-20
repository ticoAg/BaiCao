import asyncio

from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest


class StubFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]},
            "nodes": [{"id": "归经:肺经", "name": "肺经", "labels": ["归经"]}],
            "edges": [{"source": {"id": "药材:黄芩"}, "target": {"id": "归经:肺经"}, "type": "归于经脉"}],
        }

    async def read_cypher(self, query: str):
        return [{"name": "黄芩"}]


async def _run_graph_agent_returns_dual_track_output():
    agent = GraphExplorationAgent(graph_facade=StubFacade())

    result = await agent.ask(GraphAskRequest(question="黄芩归什么经？"))

    assert "肺经" in result.answer
    assert result.related_nodes[0]["name"] == "肺经"
    assert result.subgraph_meta.actual_depth >= 1


def test_graph_agent_returns_dual_track_output():
    asyncio.run(_run_graph_agent_returns_dual_track_output())


async def _run_graph_agent_records_tool_calls():
    agent = GraphExplorationAgent(graph_facade=StubFacade())

    result = await agent.ask(GraphAskRequest(question="黄芩归什么经？"))

    assert result.tool_calls[0]["tool_name"] == "search_nodes"


def test_graph_agent_records_tool_calls():
    asyncio.run(_run_graph_agent_records_tool_calls())
