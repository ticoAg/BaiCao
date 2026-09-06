"""Tests for Chat API routes (/api/v1/chat/)."""

from unittest.mock import patch

import pytest

from .helpers import assert_status


class TestChatStream:
    """POST /api/v1/chat/stream"""

    @pytest.mark.asyncio
    async def test_chat_stream_emits_agent_event_types(self, client):
        """Stream should emit agent-oriented SSE events instead of legacy reasoning/source/token events."""

        async def fake_stream_turn(question: str, session_id: str | None = None):
            assert question == "治感冒的中药有哪些"
            assert session_id is None
            yield {"type": "session", "data": {"session_id": "sid-1", "turn_id": "turn-1"}}
            yield {
                "type": "tool_start",
                "data": {
                    "call_id": "call-1",
                    "tool_name": "search_nodes",
                    "arguments": {"query": "感冒", "limit": 5},
                },
            }
            yield {
                "type": "tool_result",
                "data": {
                    "call_id": "call-1",
                    "tool_name": "search_nodes",
                    "result_summary": "返回 2 个候选节点",
                },
            }
            yield {"type": "answer_chunk", "data": {"text": "可考虑桂枝、荆芥。"}}
            yield {
                "type": "final",
                "data": {
                    "answer": "可考虑桂枝、荆芥。",
                    "provider_reasoning": [],
                    "tool_calls": [],
                    "related_nodes": [],
                    "related_edges": [],
                    "subgraph_meta": {
                        "center_node_id": None,
                        "actual_depth": 0,
                        "fallback_used": False,
                        "node_count": 0,
                        "edge_count": 0,
                    },
                    "evidence": [],
                    "reasoning_trace": [],
                    "session_id": "sid-1",
                },
            }

        with patch("app.api.chat.stream_chat_turn", side_effect=fake_stream_turn):
            resp = await client.post("/api/v1/chat/stream", json={"question": "治感冒的中药有哪些"})

        assert_status(resp, 200)
        body = resp.text
        assert "event: session" in body
        assert "event: tool_start" in body
        assert "event: tool_result" in body
        assert "event: answer_chunk" in body
        assert "event: final" in body
        assert "event: reasoning" not in body
        assert "event: sources" not in body

    @pytest.mark.asyncio
    async def test_sync_question_route_is_no_longer_available(self, client):
        resp = await client.post("/api/v1/chat/question", json={"question": "人参有什么功效？"})
        assert_status(resp, 404)

    @pytest.mark.asyncio
    async def test_graph_agent_route_is_no_longer_available(self, client):
        """Legacy graph-agent entrypoint should be removed once chat becomes the only main entry."""
        resp = await client.post("/api/v1/graph-agent/ask", json={"question": "黄芩归什么经？"})

        assert_status(resp, 404)
