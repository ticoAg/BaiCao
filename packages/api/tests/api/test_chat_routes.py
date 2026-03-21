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
