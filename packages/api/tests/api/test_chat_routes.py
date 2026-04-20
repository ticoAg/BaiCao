"""Integration tests for Chat API routes (/api/v1/chat/).

Tests mock ChatService to isolate route-level behavior:
request parsing, response structure, error handling.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from .helpers import (
    assert_status,
    assert_json_keys,
    assert_qa_response,
    make_answer_response,
    make_session_data,
)


class TestAskQuestion:
    """POST /api/v1/chat/question"""

    @pytest.mark.asyncio
    async def test_ask_question_with_body(self, client):
        """POST with JSON body should return answer response."""
        mock_response = make_answer_response()
        with patch("app.api.chat.ChatService") as MockChatService:
            instance = MockChatService.return_value
            instance.answer_question = AsyncMock(return_value=mock_response)

            resp = await client.post(
                "/api/v1/chat/question",
                json={"question": "What are the properties of ginseng?"},
            )

        assert_status(resp, 200)
        assert_qa_response(resp.json())

    @pytest.mark.asyncio
    async def test_ask_question_missing_question(self, client):
        """POST without question field should return 422."""
        resp = await client.post("/api/v1/chat/question", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_ask_question_with_session_id(self, client):
        """POST with session_id should forward it to the service."""
        sid = str(uuid4())
        mock_response = make_answer_response(session_id=sid)
        with patch("app.api.chat.ChatService") as MockChatService:
            instance = MockChatService.return_value
            instance.answer_question = AsyncMock(return_value=mock_response)

            resp = await client.post(
                "/api/v1/chat/question",
                json={"question": "Tell me about herbs", "session_id": sid},
            )

        assert_status(resp, 200)
        assert resp.json()["session_id"] == sid

    @pytest.mark.asyncio
    async def test_ask_question_can_return_workbench_frames(self, client):
        """POST should preserve optional workbench frame payloads for chat consumers."""
        mock_response = make_answer_response()
        mock_response["workbench_frames"] = [
            {
                "id": "frame-1",
                "type": "graph",
                "title": "人参图谱",
                "status": "ok",
                "payload": {
                    "graph": {"center": None, "nodes": [], "edges": []},
                    "summary": "graph",
                    "mode": "exact",
                },
            }
        ]

        with patch("app.api.chat.ChatService") as MockChatService:
            instance = MockChatService.return_value
            instance.answer_question = AsyncMock(return_value=mock_response)

            resp = await client.post(
                "/api/v1/chat/question",
                json={"question": "查人参图谱"},
            )

        assert_status(resp, 200)
        assert resp.json()["workbench_frames"][0]["type"] == "graph"


class TestGetSession:
    """GET /api/v1/chat/session/{session_id}"""

    @pytest.mark.asyncio
    async def test_get_session_found(self, client):
        """GET existing session returns session data."""
        sid = str(uuid4())
        session_data = make_session_data(sid)
        with patch("app.api.chat.ChatService") as MockChatService:
            instance = MockChatService.return_value
            instance.get_session = AsyncMock(return_value=session_data)

            resp = await client.get(f"/api/v1/chat/session/{sid}")

        assert_status(resp, 200)
        assert resp.json()["id"] == sid

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client):
        """GET non-existent session returns 404."""
        sid = str(uuid4())
        with patch("app.api.chat.ChatService") as MockChatService:
            instance = MockChatService.return_value
            instance.get_session = AsyncMock(return_value=None)

            resp = await client.get(f"/api/v1/chat/session/{sid}")

        assert_status(resp, 404)


class TestCreateSession:
    """POST /api/v1/chat/session"""

    @pytest.mark.asyncio
    async def test_create_session(self, client):
        """POST creates new session and returns session data."""
        sid = str(uuid4())
        session_data = make_session_data(sid)
        with patch("app.api.chat.ChatService") as MockChatService:
            instance = MockChatService.return_value
            instance.create_session = AsyncMock(return_value=session_data)

            resp = await client.post("/api/v1/chat/session")

        assert_status(resp, 200)
        assert_json_keys(resp.json(), {"id", "user_id", "messages", "created_at"})


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
    async def test_graph_agent_route_is_no_longer_available(self, client):
        """Legacy graph-agent entrypoint should be removed once chat becomes the only main entry."""
        resp = await client.post("/api/v1/graph-agent/ask", json={"question": "黄芩归什么经？"})

        assert_status(resp, 404)
