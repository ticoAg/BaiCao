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


@pytest.mark.asyncio
async def test_graph_agent_route_returns_abstract_query_payload(client):
    with patch("app.api.graph_agent.GraphAgentService") as service_cls:
        service_cls.return_value.ask = AsyncMock(
            return_value={
                "answer": "可考虑桂枝、荆芥。",
                "related_nodes": [{"id": "药材:桂枝", "name": "桂枝"}],
                "related_edges": [],
                "subgraph_meta": {
                    "center_node_id": "药材:桂枝",
                    "actual_depth": 1,
                    "fallback_used": False,
                    "node_count": 1,
                    "edge_count": 0,
                },
                "evidence": [],
                "reasoning_trace": [{"kind": "planner", "summary": "识别为抽象病证问题"}],
                "tool_calls": [
                    {
                        "tool_name": "graph_cypher_qa",
                        "arguments": {
                            "question": "治感冒的中药都有哪些，怎么做",
                            "generated_cypher": "MATCH (h:Herb)-[:TREATS]->(d:Disease {name:'感冒'}) RETURN h.name LIMIT 8",
                        },
                        "summary": "使用 schema-aware graph cypher agent 查询图谱",
                        "result_summary": "返回 2 个药材候选",
                        "status": "completed",
                    }
                ],
            }
        )

        response = await client.post("/api/v1/graph-agent/ask", json={"question": "治感冒的中药都有哪些，怎么做"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["tool_calls"][0]["tool_name"] == "graph_cypher_qa"
    assert payload["tool_calls"][0]["arguments"]["generated_cypher"].startswith("MATCH (h:Herb)")
