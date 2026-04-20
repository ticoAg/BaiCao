import sys
from types import SimpleNamespace

import pytest


class FakeChain:
    def __init__(self) -> None:
        self.top_k = 8

    def invoke(self, payload):
        assert payload["query"] == "治感冒的中药都有哪些，怎么做"
        assert "top_k" not in payload
        return {
            "result": "可考虑桂枝、荆芥、防风等。",
            "intermediate_steps": [
                {"context": [{"name": "桂枝"}, {"name": "荆芥"}]},
                {"note": "ignored"},
                {"query": "MATCH (h:Herb)-[:TREATS]->(d:Disease {name: '感冒'}) RETURN h.name LIMIT 8"},
            ],
        }


@pytest.mark.asyncio
async def test_graph_cypher_agent_returns_generated_cypher_and_candidates():
    from app.services.graph_cypher_agent import GraphCypherAgentService

    service = GraphCypherAgentService(chain=FakeChain())
    result = await service.answer("治感冒的中药都有哪些，怎么做")

    assert result["answer"].startswith("可考虑桂枝")
    assert "MATCH (h:Herb)" in result["generated_cypher"]
    assert result["node_names"] == ["桂枝", "荆芥"]


class FakeTopKChain:
    def __init__(self) -> None:
        self.top_k = 8
        self.seen_top_k = None
        self.seen_payload = None

    def invoke(self, payload):
        self.seen_top_k = self.top_k
        self.seen_payload = payload
        return {
            "result": "共 3 个候选。",
            "intermediate_steps": [],
        }


@pytest.mark.asyncio
async def test_graph_cypher_agent_applies_top_k_before_invoke():
    from app.services.graph_cypher_agent import GraphCypherAgentService

    chain = FakeTopKChain()
    service = GraphCypherAgentService(chain=chain)

    await service.answer("治感冒的中药都有哪些，怎么做", top_k=3)

    assert chain.seen_top_k == 3
    assert chain.seen_payload == {"query": "治感冒的中药都有哪些，怎么做"}


class FakeEmptyStepsChain:
    def invoke(self, payload):
        return {
            "result": "暂无足够图谱结果。",
            "intermediate_steps": [],
        }


@pytest.mark.asyncio
async def test_graph_cypher_agent_handles_empty_intermediate_steps():
    from app.services.graph_cypher_agent import GraphCypherAgentService

    service = GraphCypherAgentService(chain=FakeEmptyStepsChain())
    result = await service.answer("治感冒的中药都有哪些，怎么做")

    assert result["generated_cypher"] is None
    assert result["node_names"] == []
    assert result["intermediate_steps"] == []


def test_graph_cypher_agent_builds_chain_with_explicit_dangerous_flag_enabled(monkeypatch):
    from app.services.graph_cypher_agent import GraphCypherAgentService

    captured: dict[str, object] = {}

    class FakeGraphCypherQAChain:
        @classmethod
        def from_llm(cls, **kwargs):
            captured.update(kwargs)
            return object()

    class FakeNeo4jGraph:
        def __init__(self, **kwargs):
            captured["graph_kwargs"] = kwargs

    monkeypatch.setattr(
        "app.services.graph_cypher_agent.get_settings",
        lambda: SimpleNamespace(neo4j_uri="bolt://neo4j", neo4j_user="neo4j", neo4j_password="pw"),
    )
    monkeypatch.setattr("app.services.graph_cypher_agent.get_chat_model", lambda: object())
    monkeypatch.setitem(
        sys.modules,
        "langchain_neo4j",
        SimpleNamespace(GraphCypherQAChain=FakeGraphCypherQAChain, Neo4jGraph=FakeNeo4jGraph),
    )

    GraphCypherAgentService()

    assert captured["allow_dangerous_requests"] is True
