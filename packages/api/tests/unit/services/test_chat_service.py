# ChatService TDD Tests
# Test cases for ChatService (QA service with knowledge graph integration)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

pytestmark = pytest.mark.unit


class TestChatService:
    """Test suite for ChatService"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def mock_graph_service(self):
        """Create a mock graph service"""
        with patch('app.services.chat_service.graph_service') as mock:
            mock.get_herb_graph = AsyncMock(return_value={
                "center": {
                    "id": "herb-1",
                    "name": "人参",
                    "category": "补气药",
                    "source": "本草纲目",
                    "status": "verified"
                },
                "nodes": [
                    {"id": "efficacy-1", "name": "大补元气"},
                    {"id": "efficacy-2", "name": "复脉固脱"}
                ],
                "edges": [
                    {
                        "type": "HAS_EFFICACY",
                        "target": {"id": "efficacy-1", "name": "大补元气"},
                        "status": "verified"
                    },
                    {
                        "type": "HAS_EFFICACY",
                        "target": {"id": "efficacy-2", "name": "复脉固脱"},
                        "status": "verified"
                    }
                ]
            })
            yield mock

    @pytest.fixture
    def chat_service(self, mock_session, mock_graph_service):
        """Create ChatService instance with mocked dependencies"""
        from app.services.chat_service import ChatService
        return ChatService(mock_session)

    # ========== Test 1: test_answer_question_basic ==========
    @pytest.mark.asyncio
    async def test_answer_question_basic(self, chat_service, mock_graph_service):
        """Test 1: Verify complete QA flow returns expected structure"""
        result = await chat_service.answer_question("人参有什么功效？")

        # Verify response structure
        assert "answer" in result
        assert "reasoning_chain" in result
        assert "sources" in result
        assert "graph_data" in result
        assert "session_id" in result

        # Verify types
        assert isinstance(result["answer"], str)
        assert isinstance(result["reasoning_chain"], list)
        assert isinstance(result["sources"], list)
        assert isinstance(result["graph_data"], dict)
        assert isinstance(result["session_id"], str)

    # ========== Test 2: test_answer_question_with_entities ==========
    @pytest.mark.asyncio
    async def test_answer_question_with_entities(self, chat_service, mock_graph_service):
        """Test 2: Verify entity extraction integration"""
        result = await chat_service.answer_question("人参有什么功效？")

        # Verify entities were extracted from question
        assert len(result["reasoning_chain"]) > 0

        # Verify first step contains entities
        first_step = result["reasoning_chain"][0]
        assert "step" in first_step
        assert "description" in first_step
        assert "entities" in first_step

    # ========== Test 3: test_extract_entities_finds_herbs ==========
    @pytest.mark.asyncio
    async def test_extract_entities_finds_herbs(self, chat_service):
        """Test 3: Verify herb keyword detection"""
        # Test with known herb names
        herbs_to_test = ["人参", "黄芪", "当归", "陈皮", "甘草", "枸杞", "红枣", "川芎", "白术", "茯苓"]

        for herb in herbs_to_test:
            entities = await chat_service._extract_entities(f"{herb}有什么功效？")
            assert herb in entities, f"Expected {herb} to be extracted from question"

    # ========== Test 4: test_extract_entities_no_match ==========
    @pytest.mark.asyncio
    async def test_extract_entities_no_match(self, chat_service):
        """Test 4: Verify empty list when no herb keywords match"""
        entities = await chat_service._extract_entities("今天天气怎么样？")
        # Should return default (陈皮) since no herb keywords found
        assert len(entities) == 1
        assert entities[0] == "陈皮"  # Default fallback

    # ========== Test 5: test_build_reasoning_chain ==========
    @pytest.mark.asyncio
    async def test_build_reasoning_chain(self, chat_service):
        """Test 5: Verify reasoning chain structure"""
        question = "人参有什么功效？"
        entities = ["人参"]
        graph_data = {
            "center": {"name": "人参", "category": "补气药"},
            "nodes": [],
            "edges": [
                {"type": "HAS_EFFICACY", "target": {"name": "大补元气"}}
            ]
        }

        chain = await chat_service._build_reasoning_chain(question, entities, graph_data)

        # Verify chain is a list
        assert isinstance(chain, list)
        assert len(chain) >= 3  # At least 3 steps

        # Verify each step has required fields
        for step in chain:
            assert "step" in step
            assert "description" in step
            assert "confidence" in step
            assert isinstance(step["step"], int)
            assert isinstance(step["description"], str)
            assert isinstance(step["confidence"], float)
            assert 0.0 <= step["confidence"] <= 1.0

    # ========== Test 6: test_generate_answer ==========
    @pytest.mark.asyncio
    async def test_generate_answer(self, chat_service):
        """Test 6: Verify answer format"""
        question = "人参有什么功效？"
        entities = ["人参"]
        graph_data = {
            "center": {
                "name": "人参",
                "category": "补气药",
                "source": "本草纲目",
                "status": "verified"
            },
            "nodes": [],
            "edges": [
                {"type": "HAS_EFFICACY", "target": {"name": "大补元气"}},
                {"type": "HAS_FLAVOR", "target": {"name": "甘"}}
            ]
        }
        reasoning_chain = [
            {"step": 1, "description": "识别问题类型：功效查询", "entities": ["人参"], "confidence": 0.95}
        ]

        answer = await chat_service._generate_answer(question, entities, graph_data, reasoning_chain)

        # Verify answer is a non-empty string
        assert isinstance(answer, str)
        assert len(answer) > 0
        # Answer should mention the herb name
        assert "人参" in answer

    # ========== Test 7: test_collect_sources ==========
    @pytest.mark.asyncio
    async def test_collect_sources(self, chat_service):
        """Test 7: Verify source aggregation"""
        graph_data = {
            "center": {
                "name": "人参",
                "source": "本草纲目"
            },
            "nodes": [],
            "edges": []
        }

        sources = await chat_service._collect_sources(graph_data)

        # Verify sources is a list
        assert isinstance(sources, list)

        # If center has source, should be included
        if graph_data["center"].get("source"):
            assert len(sources) >= 1
            source = sources[0]
            assert "id" in source
            assert "name" in source
            assert "citation" in source
            assert source["name"] == "本草纲目"

    # ========== Test 8: test_session_id_generation ==========
    @pytest.mark.asyncio
    async def test_session_id_generation(self, chat_service, mock_graph_service):
        """Test 8: Verify new session UUID generation"""
        # When session_id is not provided, a new UUID should be generated
        result1 = await chat_service.answer_question("人参有什么功效？")
        result2 = await chat_service.answer_question("黄芪有什么功效？")

        # Both should have session_id
        assert "session_id" in result1
        assert "session_id" in result2

        # session_ids should be valid UUIDs
        try:
            UUID(result1["session_id"])
            UUID(result2["session_id"])
        except ValueError:
            pytest.fail("session_id is not a valid UUID")

        # Each call should generate different session_id
        assert result1["session_id"] != result2["session_id"]

    # ========== Additional verification tests ==========

    @pytest.mark.asyncio
    async def test_answer_with_provided_session_id(self, chat_service, mock_graph_service):
        """Verify that provided session_id is used instead of generating new one"""
        specific_session_id = "test-session-123"
        result = await chat_service.answer_question(
            "人参有什么功效？",
            session_id=specific_session_id
        )

        assert result["session_id"] == specific_session_id

    @pytest.mark.asyncio
    async def test_reasoning_chain_has_correct_steps(self, chat_service):
        """Verify reasoning chain steps are numbered correctly"""
        graph_data = {
            "center": {"name": "人参"},
            "nodes": [],
            "edges": [{"type": "HAS_EFFICACY", "target": {"name": "补气"}}]
        }

        chain = await chat_service._build_reasoning_chain(
            "人参有什么功效？",
            ["人参"],
            graph_data
        )

        # Steps should be in ascending order
        steps = [step["step"] for step in chain]
        assert steps == list(range(1, len(steps) + 1))

    @pytest.mark.asyncio
    async def test_validate_response_missing_keys(self, chat_service):
        """Verify validation raises error for missing required keys"""
        invalid_response = {
            "answer": "test",
            # Missing other required keys
        }
        with pytest.raises(ValueError, match="Response missing required keys"):
            chat_service._validate_response(invalid_response)

    @pytest.mark.asyncio
    async def test_validate_response_invalid_types(self, chat_service):
        """Verify validation raises error for invalid types"""
        invalid_response = {
            "answer": 123,  # Should be string
            "reasoning_chain": "not a list",
            "sources": "not a list",
            "graph_data": "not a dict",
            "session_id": 456
        }
        with pytest.raises(ValueError):
            chat_service._validate_response(invalid_response)

    @pytest.mark.asyncio
    async def test_query_knowledge_graph_empty_entities(self, chat_service):
        """Verify empty entities returns empty graph data"""
        result = await chat_service._query_knowledge_graph([])
        assert result == {"center": None, "nodes": [], "edges": []}

    @pytest.mark.asyncio
    async def test_extract_entities_returns_default_when_no_match(self, chat_service):
        """Verify default herb is returned when no herb keywords match"""
        entities = await chat_service._extract_entities("今天天气怎么样？")
        assert entities == ["陈皮"]

    @pytest.mark.asyncio
    async def test_build_reasoning_chain_empty_graph(self, chat_service):
        """Verify reasoning chain builds correctly with empty graph"""
        chain = await chat_service._build_reasoning_chain(
            "测试问题",
            ["测试药材"],
            {"center": None, "nodes": [], "edges": []}
        )
        # Should still have steps even without graph data
        assert len(chain) >= 1
