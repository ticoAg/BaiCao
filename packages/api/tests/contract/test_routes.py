"""
API Routes TDD Tests

Red Phase: These tests define the expected behavior of Chat, Graph, and Herb API routes.
They should FAIL initially if implementation is incomplete.
Green Phase: Implement methods to make tests pass.
Refactor Phase: Improve code quality while keeping tests green.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

pytestmark = pytest.mark.contract


# ============ Helper Functions (Refactor Phase) ============

async def assert_response_structure(response, expected_keys):
    """Assert that response contains expected keys."""
    data = response.json()
    for key in expected_keys:
        assert key in data, f"Response missing key: {key}"
    return data


async def assert_pagination_structure(data):
    """Assert that paginated response has correct structure and return data."""
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "has_more" in data
    assert isinstance(data["items"], list)
    return data


def create_mock_herb(herb_id=None, name="人参", category="补气药"):
    """Create a consistent mock herb object."""
    return {
        "id": str(herb_id or uuid4()),
        "name": name,
        "latin_name": "Panax ginseng",
        "category": category,
        "description": "人参是一种珍贵的中药材",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


def create_mock_graph_response(herb_name="人参"):
    """Create a consistent mock graph response."""
    return {
        "center": {
            "id": str(uuid4()),
            "name": herb_name,
            "labels": ["Herb"],
            "status": "verified"
        },
        "nodes": [
            {"id": str(uuid4()), "name": "人参皂苷", "labels": ["Component"]},
            {"id": str(uuid4()), "name": "补气", "labels": ["Efficacy"]}
        ],
        "edges": [
            {
                "id": str(uuid4()),
                "type": "包含成分",
                "start": str(uuid4()),
                "end": str(uuid4()),
                "status": "verified"
            }
        ]
    }


def create_mock_chat_response(session_id=None):
    """Create a consistent mock chat response."""
    return {
        "answer": "关于人参的信息：\n- 分类：补气药\n- 主要功效：补气",
        "reasoning_chain": [
            {
                "step": 1,
                "description": "识别问题类型：功效查询",
                "entities": ["人参"],
                "confidence": 0.95
            },
            {
                "step": 2,
                "description": "在知识图谱中查找相关实体",
                "entities": ["人参"],
                "confidence": 0.90
            }
        ],
        "sources": [
            {"id": str(uuid4()), "name": "本草纲目", "citation": "来源：本草纲目"}
        ],
        "graph_data": create_mock_graph_response(),
        "session_id": session_id or str(uuid4())
    }


# ============ Chat API Tests ============

@pytest.mark.asyncio
async def test_ask_question(client, mock_db):
    """Test POST /api/v1/chat/question returns answer with reasoning chain."""
    question = "人参有什么功效？"
    session_id = str(uuid4())

    with patch("app.services.chat_service.graph_service") as mock_graph:
        mock_graph.get_herb_graph = AsyncMock(return_value=create_mock_graph_response())

        response = await client.post(
            "/api/v1/chat/question",
            params={"question": question, "session_id": session_id}
        )

    assert response.status_code == 200
    data = await assert_response_structure(response, ["answer", "reasoning_chain", "sources", "graph_data", "session_id"])
    assert isinstance(data["reasoning_chain"], list)
    assert isinstance(data["sources"], list)
    assert data["session_id"] == session_id


@pytest.mark.asyncio
async def test_get_session_found(client, mock_db):
    """Test GET /api/v1/chat/session/{session_id} returns session data."""
    session_id = str(uuid4())
    mock_session = {
        "id": session_id,
        "user_id": "user-123",
        "messages": [
            {"role": "user", "content": "人参有什么功效？"},
            {"role": "assistant", "content": "人参能大补元气"}
        ],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    with patch("app.api.chat.ChatService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_session = AsyncMock(return_value=mock_session)

        response = await client.get(f"/api/v1/chat/session/{session_id}")

    assert response.status_code == 200
    data = await assert_response_structure(response, ["id", "user_id", "messages", "created_at"])
    assert data["id"] == session_id


@pytest.mark.asyncio
async def test_get_session_not_found(client, mock_db):
    """Test GET /api/v1/chat/session/{session_id} returns 404 for non-existent session."""
    session_id = str(uuid4())

    with patch("app.api.chat.ChatService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_session = AsyncMock(return_value=None)

        response = await client.get(f"/api/v1/chat/session/{session_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_create_session(client, mock_db):
    """Test POST /api/v1/chat/session creates new session."""
    user_id = "user-123"
    mock_session = {
        "id": str(uuid4()),
        "user_id": user_id,
        "messages": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    with patch("app.api.chat.ChatService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.create_session = AsyncMock(return_value=mock_session)

        response = await client.post("/api/v1/chat/session", params={"user_id": user_id})

    assert response.status_code == 200
    data = await assert_response_structure(response, ["id", "user_id", "messages", "created_at"])
    assert data["user_id"] == user_id


# ============ Graph API Tests ============

@pytest.mark.asyncio
async def test_get_herb_graph(client):
    """Test GET /api/v1/graph/herb/{name} returns herb graph data."""
    herb_name = "人参"
    mock_graph = create_mock_graph_response(herb_name)

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.get_herb_graph = AsyncMock(return_value=mock_graph)

        response = await client.get(f"/api/v1/graph/herb/{herb_name}")

    assert response.status_code == 200
    data = await assert_response_structure(response, ["center", "nodes", "edges"])
    assert data["center"]["name"] == herb_name


@pytest.mark.asyncio
async def test_get_herb_graph_not_found(client):
    """Test GET /api/v1/graph/herb/{name} returns 404 for non-existent herb."""
    herb_name = "不存在的药材"

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.get_herb_graph = AsyncMock(return_value={"center": None, "nodes": [], "edges": []})

        response = await client.get(f"/api/v1/graph/herb/{herb_name}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_search_nodes(client):
    """Test GET /api/v1/graph/search returns matching nodes."""
    query = "人参"
    mock_results = [
        {"node": {"id": str(uuid4()), "name": "人参", "labels": ["Herb"]}, "labels": ["Herb"]},
        {"node": {"id": str(uuid4()), "name": "人参皂苷", "labels": ["Component"]}, "labels": ["Component"]}
    ]

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.search_nodes = AsyncMock(return_value=mock_results)

        response = await client.get("/api/v1/graph/search", params={"q": query})

    assert response.status_code == 200
    data = await assert_response_structure(response, ["items", "total"])
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_search_nodes_with_label(client):
    """Test GET /api/v1/graph/search with label filter."""
    query = "人"
    label = "Herb"
    mock_results = [
        {"node": {"id": str(uuid4()), "name": "人参", "labels": ["Herb"]}, "labels": ["Herb"]}
    ]

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.search_nodes = AsyncMock(return_value=mock_results)

        response = await client.get("/api/v1/graph/search", params={"q": query, "label": label})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_node(client):
    """Test GET /api/v1/graph/node/{node_id} returns node data."""
    node_id = str(uuid4())
    mock_node = {
        "id": node_id,
        "name": "人参",
        "labels": ["Herb"],
        "status": "verified"
    }

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.get_node = AsyncMock(return_value=mock_node)

        response = await client.get(f"/api/v1/graph/node/{node_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == node_id
    assert data["name"] == "人参"


@pytest.mark.asyncio
async def test_get_node_not_found(client):
    """Test GET /api/v1/graph/node/{node_id} returns 404 for non-existent node."""
    node_id = str(uuid4())

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.get_node = AsyncMock(return_value=None)

        response = await client.get(f"/api/v1/graph/node/{node_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_pending_nodes(client):
    """Test GET /api/v1/graph/pending?type=nodes returns pending nodes."""
    mock_nodes = [
        {"node": {"id": str(uuid4()), "name": "待验证药材1", "labels": ["Herb"]}, "labels": ["Herb"]},
        {"node": {"id": str(uuid4()), "name": "待验证药材2", "labels": ["Herb"]}, "labels": ["Herb"]}
    ]

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.get_pending_nodes = AsyncMock(return_value=mock_nodes)

        response = await client.get("/api/v1/graph/pending", params={"type": "nodes"})

    assert response.status_code == 200
    data = await assert_response_structure(response, ["items", "type"])
    assert data["type"] == "nodes"
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_pending_relationships(client):
    """Test GET /api/v1/graph/pending?type=relationships returns pending relationships."""
    mock_relationships = [
        {"id": str(uuid4()), "type": "包含成分", "status": "pending"},
        {"id": str(uuid4()), "type": "具有功效", "status": "pending"}
    ]

    with patch("app.api.graph.graph_service") as mock_graph_service:
        mock_graph_service.get_pending_relationships = AsyncMock(return_value=mock_relationships)

        response = await client.get("/api/v1/graph/pending", params={"type": "relationships"})

    assert response.status_code == 200
    data = await assert_response_structure(response, ["items", "type"])
    assert data["type"] == "relationships"
    assert len(data["items"]) == 2


# ============ Herb API Tests ============

@pytest.mark.asyncio
async def test_get_herb(client, mock_db):
    """Test GET /api/v1/herbs/{herb_id} returns herb data."""
    herb_id = uuid4()
    mock_herb = create_mock_herb(herb_id)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_herb)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.herb.HerbService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_by_id = AsyncMock(return_value=mock_herb)

        response = await client.get(f"/api/v1/herbs/{herb_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "人参"


@pytest.mark.asyncio
async def test_get_herb_not_found(client, mock_db):
    """Test GET /api/v1/herbs/{herb_id} returns 404 for non-existent herb."""
    herb_id = uuid4()

    with patch("app.api.herb.HerbService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_by_id = AsyncMock(return_value=None)

        response = await client.get(f"/api/v1/herbs/{herb_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_list_herbs(client, mock_db):
    """Test GET /api/v1/herbs/ returns paginated herb list."""
    herbs = [
        create_mock_herb(uuid4(), "人参", "补气药"),
        create_mock_herb(uuid4(), "黄芪", "补气药")
    ]
    total = 2

    with patch("app.api.herb.HerbService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_herbs = AsyncMock(return_value=(herbs, total))

        response = await client.get("/api/v1/herbs/")

    assert response.status_code == 200
    data = await assert_pagination_structure(response.json())
    assert len(data["items"]) == 2
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_herbs_with_category(client, mock_db):
    """Test GET /api/v1/herbs/?category=xxx filters by category."""
    category = "补气药"
    herbs = [create_mock_herb(uuid4(), "人参", category)]
    total = 1

    with patch("app.api.herb.HerbService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_herbs = AsyncMock(return_value=(herbs, total))

        response = await client.get("/api/v1/herbs/", params={"category": category})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    for item in data["items"]:
        assert item["category"] == category


@pytest.mark.asyncio
async def test_list_herbs_with_pagination(client, mock_db):
    """Test GET /api/v1/herbs/?limit=X&offset=Y with pagination."""
    herbs = [create_mock_herb(uuid4(), "人参", "补气药")]
    total = 100

    with patch("app.api.herb.HerbService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_herbs = AsyncMock(return_value=(herbs, total))

        response = await client.get("/api/v1/herbs/", params={"limit": 1, "offset": 0})

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 100
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert data["has_more"] is True
