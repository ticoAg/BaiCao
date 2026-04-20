import asyncio

from graph_runtime.agent.graph_agent import GraphExplorationAgent
from graph_runtime.contracts.inputs import GraphAskRequest


class StubFacade:
    def __init__(self) -> None:
        self.search_queries: list[str] = []
        self.cypher_queries: list[str] = []

    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        self.search_queries.append(query)
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]},
            "nodes": [{"id": "归经:肺经", "name": "肺经", "labels": ["归经"]}],
            "edges": [{"source": {"id": "药材:黄芩"}, "target": {"id": "归经:肺经"}, "type": "归于经脉"}],
        }

    async def read_cypher(self, query: str):
        self.cypher_queries.append(query)
        return [{"name": "黄芩"}]


class LoopingFacade(StubFacade):
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        self.search_queries.append(query)
        if query == "黄芩":
            return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]
        return []


class ComplexFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": f"药材:{query}", "name": query, "labels": ["药材"]}] if query in {"桂枝", "荆芥"} else []

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": node_id, "name": node_id.split(":", 1)[1], "labels": ["药材"]},
            "nodes": [{"id": node_id, "name": node_id.split(":", 1)[1], "labels": ["药材"]}],
            "edges": [],
        }

    async def read_cypher(self, query: str):
        return []


class FakeCypherAgent:
    async def answer(self, question: str, top_k: int = 8):
        return {
            "answer": "可考虑桂枝、荆芥，并结合发汗解表思路处理。",
            "generated_cypher": "MATCH (h)-[:TREATS]->(d {name:'感冒'}) RETURN h.name LIMIT 8",
            "node_names": ["桂枝", "荆芥"],
            "intermediate_steps": [],
        }


async def _run_graph_agent_returns_dual_track_output():
    agent = GraphExplorationAgent(graph_facade=StubFacade())

    result = await agent.ask(GraphAskRequest(question="黄芩归什么经？"))

    assert "肺经" in result.answer
    assert result.related_nodes[0]["name"] == "肺经"
    assert result.subgraph_meta.actual_depth >= 1


def test_graph_agent_returns_dual_track_output():
    asyncio.run(_run_graph_agent_returns_dual_track_output())


async def _run_graph_agent_records_tool_calls():
    facade = StubFacade()
    agent = GraphExplorationAgent(graph_facade=facade)

    result = await agent.ask(GraphAskRequest(question="黄芩归什么经？"))

    assert result.tool_calls[0].tool_name == "search_nodes"
    assert result.tool_calls[0].arguments["query"] == "黄芩"
    assert result.tool_calls[1].tool_name == "expand_neighbors"
    assert result.tool_calls[1].arguments["node_id"] == "药材:黄芩"


def test_graph_agent_records_tool_calls():
    asyncio.run(_run_graph_agent_records_tool_calls())


async def _run_graph_agent_loops_until_graph_tool_succeeds():
    facade = LoopingFacade()
    agent = GraphExplorationAgent(graph_facade=facade)

    result = await agent.ask(GraphAskRequest(question="请告诉我黄芩归什么经？", tool_call_budget=6))

    assert facade.search_queries[0] == "黄芩"
    assert result.tool_calls[0].arguments["query"] == "黄芩"
    assert result.tool_calls[0].result_summary.startswith("命中 1 个候选")
    assert result.subgraph_meta.center_node_id == "药材:黄芩"


def test_graph_agent_loops_until_graph_tool_succeeds():
    asyncio.run(_run_graph_agent_loops_until_graph_tool_succeeds())


async def _run_graph_agent_uses_readonly_cypher_as_fallback():
    facade = LoopingFacade()
    agent = GraphExplorationAgent(graph_facade=facade)

    result = await agent.ask(GraphAskRequest(question="完全未知问题", tool_call_budget=6))

    assert facade.cypher_queries
    assert any(call.tool_name == "read_cypher" for call in result.tool_calls)
    assert result.tool_calls[-2].tool_name == "search_nodes"
    assert result.tool_calls[-1].tool_name == "expand_neighbors"
    assert result.subgraph_meta.center_node_id == "药材:黄芩"


def test_graph_agent_uses_readonly_cypher_as_fallback():
    asyncio.run(_run_graph_agent_uses_readonly_cypher_as_fallback())


async def _run_graph_agent_uses_graph_cypher_qa_for_abstract_query():
    agent = GraphExplorationAgent(graph_facade=ComplexFacade(), cypher_agent=FakeCypherAgent())

    result = await agent.ask(GraphAskRequest(question="治感冒的中药都有哪些，怎么做", tool_call_budget=8))

    assert result.tool_calls[0].tool_name == "graph_cypher_qa"
    assert "generated_cypher" in result.tool_calls[0].arguments
    assert result.related_nodes[0]["name"] == "桂枝"
    assert "桂枝" in result.answer


def test_graph_agent_uses_graph_cypher_qa_for_abstract_query():
    asyncio.run(_run_graph_agent_uses_graph_cypher_qa_for_abstract_query())
