# ChatService TDD Tests
# 8 test cases covering the QA pipeline with knowledge graph integration

import pytest
from unittest.mock import AsyncMock, patch
from uuid import UUID


# ============ Test fixtures ============

@pytest.fixture
def mock_graph_data():
    """Predefined herb graph data returned by graph_service.get_herb_graph"""
    return {
        "center": {
            "name": "陈皮",
            "id": "herb-001",
            "category": "理气药",
            "source": "中国药典2020",
            "status": "verified",
            "labels": ["Herb"],
        },
        "nodes": [
            {
                "name": "陈皮",
                "id": "herb-001",
                "category": "理气药",
                "source": "中国药典2020",
                "status": "verified",
                "labels": ["Herb"],
            },
            {
                "name": "理气",
                "id": "eff-001",
                "source": "中国药典2020",
                "status": "pending",
                "labels": ["Efficacy"],
            },
            {
                "name": "苦",
                "id": "flv-001",
                "source": "中国药典2020",
                "status": "pending",
                "labels": ["Flavor"],
            },
        ],
        "edges": [
            {
                "id": "edge-001",
                "rel_type": "具有功效",
                "status": "pending",
                "source": {"id": "herb-001", "name": "陈皮", "labels": ["Herb"]},
                "target": {"id": "eff-001", "name": "理气", "labels": ["Efficacy"]},
            },
            {
                "id": "edge-002",
                "rel_type": "具有性味",
                "status": "pending",
                "source": {"id": "herb-001", "name": "陈皮", "labels": ["Herb"]},
                "target": {"id": "flv-001", "name": "苦", "labels": ["Flavor"]},
            },
        ],
    }


@pytest.fixture
def mock_graph_service(mock_graph_data):
    """Mock graph_service singleton to return predefined graph data"""
    mock_svc = AsyncMock()
    mock_svc.get_herb_graph = AsyncMock(return_value=mock_graph_data)
    return mock_svc


@pytest.fixture
def mock_db():
    """Mock AsyncSession for ChatService constructor"""
    session = AsyncMock()
    return session


# ============ Test Cases ============


class TestChatServiceAnswerQuestion:
    """Tests for the full answer_question pipeline"""

    @pytest.mark.asyncio
    async def test_answer_question_basic(self, mock_db, mock_graph_service, mock_graph_data):
        """Test full pipeline with a simple question returns expected structure"""
        with patch("app.services.chat_service.graph_service", mock_graph_service):
            from app.services.chat_service import ChatService

            svc = ChatService(mock_db)
            result = await svc.answer_question("陈皮有什么功效？")

        # Verify response structure
        assert "answer" in result
        assert "reasoning_chain" in result
        assert "sources" in result
        assert "graph_data" in result
        assert "session_id" in result

        # answer should be a non-empty string
        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

        # reasoning_chain should be a non-empty list
        assert isinstance(result["reasoning_chain"], list)
        assert len(result["reasoning_chain"]) > 0

        # graph_data should contain the center node
        assert result["graph_data"]["center"] is not None
        assert result["graph_data"]["center"]["name"] == "陈皮"

        # graph_service.get_herb_graph was called
        mock_graph_service.get_herb_graph.assert_called()

    @pytest.mark.asyncio
    async def test_answer_question_with_entities(self, mock_db, mock_graph_service):
        """Test pipeline with a question containing specific herb entity"""
        with patch("app.services.chat_service.graph_service", mock_graph_service):
            from app.services.chat_service import ChatService

            svc = ChatService(mock_db)
            await svc.answer_question("人参的功效和作用是什么？")

        # Should have called get_herb_graph with the detected entity
        mock_graph_service.get_herb_graph.assert_called()
        first_call_args = mock_graph_service.get_herb_graph.call_args_list[0]
        assert first_call_args[0][0] == "人参"

    @pytest.mark.asyncio
    async def test_session_id_generation(self, mock_db, mock_graph_service):
        """Test that a new UUID session_id is generated when none provided"""
        with patch("app.services.chat_service.graph_service", mock_graph_service):
            from app.services.chat_service import ChatService

            svc = ChatService(mock_db)
            result = await svc.answer_question("陈皮有什么功效？")

        session_id = result["session_id"]
        # Should be a valid UUID string
        parsed = UUID(session_id)
        assert str(parsed) == session_id

    @pytest.mark.asyncio
    async def test_session_id_preserved(self, mock_db, mock_graph_service):
        """Test that provided session_id is preserved in response"""
        with patch("app.services.chat_service.graph_service", mock_graph_service):
            from app.services.chat_service import ChatService

            svc = ChatService(mock_db)
            result = await svc.answer_question("陈皮？", session_id="my-session-123")

        assert result["session_id"] == "my-session-123"

    @pytest.mark.asyncio
    async def test_answer_question_includes_workbench_frames(self, mock_db, mock_graph_service):
        """Test chat responses expose reusable workbench frame payloads."""
        with (
            patch("app.services.chat_service.graph_service", mock_graph_service),
            patch("app.services.chat_service.workbench_service") as mock_workbench_service,
            patch("app.services.chat_service.is_llm_available", return_value=False),
        ):
            mock_workbench_service.execute = AsyncMock(
                return_value={
                    "command": "查陈皮图谱",
                    "frames": [
                        {
                            "id": "frame-1",
                            "type": "graph",
                            "title": "陈皮图谱",
                            "status": "ok",
                            "payload": {
                                "graph": mock_graph_service.get_herb_graph.return_value,
                                "summary": "graph",
                                "mode": "exact",
                            },
                        }
                    ],
                    "history_item": {"command": "查陈皮图谱", "source": "chat"},
                }
            )

            from app.services.chat_service import ChatService

            svc = ChatService(mock_db)
            result = await svc.answer_question("陈皮有什么功效？")

        assert "workbench_frames" in result
        assert result["workbench_frames"][0]["type"] == "graph"


class TestChatServiceExtractEntities:
    """Tests for _extract_entities method"""

    @pytest.mark.asyncio
    async def test_extract_entities_finds_herbs(self, mock_db):
        """Test that herb keywords in question are correctly extracted"""
        from app.services.chat_service import ChatService

        svc = ChatService(mock_db)
        entities = await svc._extract_entities("人参和黄芪能一起泡水喝吗？")

        assert "人参" in entities
        assert "黄芪" in entities
        assert len(entities) == 2

    @pytest.mark.asyncio
    async def test_extract_entities_no_match(self, mock_db):
        """Test that unknown entities fall back to default herb"""
        from app.services.chat_service import ChatService

        svc = ChatService(mock_db)
        entities = await svc._extract_entities("今天天气怎么样？")

        # Should fall back to DEFAULT_HERB
        from app.services.chat_service import DEFAULT_HERB
        assert entities == [DEFAULT_HERB]


class TestChatServiceBuildReasoningChain:
    """Tests for _build_reasoning_chain method"""

    @pytest.mark.asyncio
    async def test_build_reasoning_chain(self, mock_db, mock_graph_data):
        """Test reasoning chain has correct structure with step numbers"""
        from app.services.chat_service import ChatService

        svc = ChatService(mock_db)
        chain = await svc._build_reasoning_chain(
            "陈皮有什么功效？", ["陈皮"], mock_graph_data
        )

        # Should have multiple steps
        assert isinstance(chain, list)
        assert len(chain) >= 2

        # Each step should have required fields
        for step in chain:
            assert "step" in step
            assert "description" in step
            assert "confidence" in step
            assert isinstance(step["confidence"], float)
            assert 0.0 <= step["confidence"] <= 1.0

        # Steps should be numbered sequentially
        step_numbers = [s["step"] for s in chain]
        assert step_numbers == sorted(step_numbers)
        assert step_numbers[0] == 1


class TestChatServiceGenerateAnswer:
    """Tests for _generate_answer method"""

    @pytest.mark.asyncio
    async def test_generate_answer(self, mock_db, mock_graph_data):
        """Test simplified answer generation contains herb info"""
        from app.services.chat_service import ChatService

        svc = ChatService(mock_db)
        chain = await svc._build_reasoning_chain(
            "陈皮有什么功效？", ["陈皮"], mock_graph_data
        )
        answer = await svc._generate_answer(
            "陈皮有什么功效？", ["陈皮"], mock_graph_data, chain
        )

        assert isinstance(answer, str)
        assert len(answer) > 0
        # Answer should mention the herb
        assert "陈皮" in answer


class TestChatServiceCollectSources:
    """Tests for _collect_sources method"""

    @pytest.mark.asyncio
    async def test_collect_sources(self, mock_db, mock_graph_data):
        """Test source collection from graph data"""
        from app.services.chat_service import ChatService

        svc = ChatService(mock_db)
        sources = await svc._collect_sources(mock_graph_data)

        assert isinstance(sources, list)
        # Center node has source="中国药典2020", so at least 1 source expected
        assert len(sources) >= 1

        for src in sources:
            assert "id" in src
            assert "name" in src
            assert "citation" in src
