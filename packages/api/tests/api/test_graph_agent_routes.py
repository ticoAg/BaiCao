from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_graph_agent_route_returns_answer_payload(client):
    with patch("app.api.graph_agent.GraphAgentService") as service_cls:
        service_cls.return_value.ask = AsyncMock(
            return_value={
                "answer": "黄芩相关结果：肺经。",
                "related_nodes": [{"id": "归经:肺经", "name": "肺经"}],
                "related_edges": [],
                "subgraph_meta": {
                    "center_node_id": "药材:黄芩",
                    "actual_depth": 1,
                    "fallback_used": False,
                    "node_count": 1,
                    "edge_count": 0,
                },
                "evidence": [],
                "reasoning_trace": [],
                "tool_calls": [],
            }
        )

        response = await client.post("/api/v1/graph-agent/ask", json={"question": "黄芩归什么经？"})

    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert "related_nodes" in payload
