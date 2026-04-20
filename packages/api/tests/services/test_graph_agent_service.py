import pytest


class FakeGraphFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        if query == "桂枝":
            return [{"id": "药材:桂枝", "name": "桂枝", "labels": ["药材"]}]
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        herb_name = node_id.split(":", 1)[1]
        return {
            "center": {"id": node_id, "name": herb_name, "labels": ["药材"]},
            "nodes": [{"id": node_id, "name": herb_name, "labels": ["药材"]}],
            "edges": [],
        }


class FakeCypherAgent:
    async def answer(self, question: str, top_k: int = 8):
        return {
            "answer": "可考虑桂枝。",
            "generated_cypher": "MATCH (h:Herb)-[:TREATS]->(d:Disease {name:'感冒'}) RETURN h.name LIMIT 8",
            "node_names": ["桂枝"],
            "intermediate_steps": [],
        }


@pytest.mark.asyncio
async def test_graph_agent_service_returns_dual_track_payload():
    from app.services.graph_agent_service import GraphAgentService

    service = GraphAgentService(graph_facade=FakeGraphFacade())
    result = await service.ask("黄芩归什么经？")

    assert "answer" in result
    assert "related_nodes" in result
    assert "subgraph_meta" in result


@pytest.mark.asyncio
async def test_graph_agent_service_supports_abstract_query_payload():
    from app.services.graph_agent_service import GraphAgentService

    service = GraphAgentService(graph_facade=FakeGraphFacade(), cypher_agent=FakeCypherAgent())
    payload = await service.ask("治感冒的中药都有哪些，怎么做")

    assert payload["tool_calls"][0]["tool_name"] == "graph_cypher_qa"
    assert payload["tool_calls"][0]["arguments"]["generated_cypher"].startswith("MATCH (h:Herb)")
    assert payload["related_nodes"][0]["name"] == "桂枝"
