import pytest


class FakeGraphFacade:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": node_id, "name": "黄芩", "labels": ["药材"]},
            "nodes": [{"id": "归经:肺经", "name": "肺经", "labels": ["归经"]}],
            "edges": [{"source": {"id": node_id}, "target": {"id": "归经:肺经"}, "type": "归于经脉"}],
        }


@pytest.mark.asyncio
async def test_graph_agent_service_returns_dual_track_payload():
    from app.services.graph_agent_service import GraphAgentService

    service = GraphAgentService(graph_facade=FakeGraphFacade())
    result = await service.ask("黄芩归什么经？")

    assert "answer" in result
    assert "related_nodes" in result
    assert "subgraph_meta" in result
