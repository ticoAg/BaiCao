"""
GraphService TDD Tests

Red Phase: These tests define the expected behavior of GraphService.
They should FAIL initially because the implementation is incomplete.
Green Phase: Implement methods to make tests pass.
Refactor Phase: Improve code quality while keeping tests green.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.kg.graph_service import GraphService
from app.models.enums import NodeStatus, HerbType

pytestmark = pytest.mark.unit


# ============ Fixtures ============

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver"""
    driver = MagicMock()
    session = MagicMock()
    session.run = AsyncMock()
    session.close = AsyncMock()
    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()
    return driver


@pytest.fixture
def graph_service(mock_neo4j_driver):
    """GraphService with mocked Neo4j driver"""
    service = GraphService()
    service.driver = mock_neo4j_driver
    return service


# ============ Test Cases ============

@pytest.mark.asyncio
async def test_create_node(graph_service, mock_neo4j_driver):
    """Test creating a basic node with required fields"""
    node_id = str(uuid4())
    mock_node = {
        "id": node_id,
        "name": "TestNode",
        "source": "test_source",
        "status": "pending"
    }
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "n": mock_node
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.create_node(
        label="TestLabel",
        name="TestNode",
        source="test_source"
    )

    assert result["name"] == "TestNode"
    assert result["source"] == "test_source"
    assert result["status"] == "pending"
    mock_session.run.assert_called_once()


@pytest.mark.asyncio
async def test_get_node(graph_service, mock_neo4j_driver):
    """Test retrieving a node by ID"""
    node_id = str(uuid4())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "n": {"id": node_id, "name": "TestNode", "status": "pending"},
        "labels": ["TestLabel"]
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.get_node(node_id)

    assert result["id"] == node_id
    assert result["name"] == "TestNode"
    assert result["labels"] == ["TestLabel"]


@pytest.mark.asyncio
async def test_get_node_not_found(graph_service, mock_neo4j_driver):
    """Test that get_node returns None when node does not exist"""
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.get_node("nonexistent-id")

    assert result is None


@pytest.mark.asyncio
async def test_create_herb(graph_service, mock_neo4j_driver):
    """Test creating a herb node with proper type"""
    node_id = str(uuid4())
    mock_node = {
        "id": node_id,
        "name": "RenShen",
        "source": "bencao",
        "type": "base",
        "category": "qi",
        "status": "pending"
    }
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "n": mock_node
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.create_herb(
        name="RenShen",
        source="bencao",
        herb_type=HerbType.BASE,
        category="qi"
    )

    assert result["name"] == "RenShen"
    assert result["type"] == "base"
    assert result["category"] == "qi"
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_create_relationship(graph_service):
    """Test generic relationship creation delegates to neomodel manager"""
    from_node = MagicMock()
    rel_manager = MagicMock()
    rel_manager.connect = AsyncMock(return_value=MagicMock(__properties__={"status": "pending"}))
    from_node.has_efficacy = rel_manager
    to_node = MagicMock()

    herb_model = MagicMock()
    herb_model.nodes.get = AsyncMock(return_value=from_node)
    efficacy_model = MagicMock()
    efficacy_model.nodes.get = AsyncMock(return_value=to_node)

    with patch.dict(
        "app.kg.graph_service.NODE_MODEL_MAP",
        {"Herb": herb_model, "Efficacy": efficacy_model},
        clear=False,
    ):
        result = await graph_service.create_relationship(
            "Herb", "RenShen", "Efficacy", "BuQi", "具有功效"
        )

    assert result["status"] == "pending"
    assert result["type"] == "具有功效"
    rel_manager.connect.assert_awaited_once()


@pytest.mark.asyncio
async def test_link_herb_parent(graph_service):
    """Test linking herb to parent using 父类 relationship"""
    graph_service.create_relationship = AsyncMock(
        return_value={"type": "父类", "status": "pending"}
    )

    result = await graph_service.link_herb_parent(
        child_name="RenShen",
        parent_name="Ginseng"
    )

    assert result["type"] == "父类"
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "RenShen", "Herb", "Ginseng", "父类"
    )


@pytest.mark.asyncio
async def test_link_herb_child(graph_service):
    """Test linking herb to child using 子类 relationship"""
    graph_service.create_relationship = AsyncMock(
        return_value={"type": "子类", "status": "pending"}
    )

    result = await graph_service.link_herb_child(
        parent_name="Ginseng",
        child_name="RenShen"
    )

    assert result["type"] == "子类"
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "Ginseng", "Herb", "RenShen", "子类"
    )


@pytest.mark.asyncio
async def test_link_herb_source(graph_service):
    """Test linking herb to source using 来源于 relationship"""
    graph_service.create_relationship = AsyncMock(
        return_value={"type": "来源于", "status": "pending"}
    )

    result = await graph_service.link_herb_source(
        herb_name="RenShen",
        source_name="Jilin"
    )

    assert result["type"] == "来源于"
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "RenShen", "Source", "Jilin", "来源于"
    )


@pytest.mark.asyncio
async def test_get_herb_graph(graph_service, mock_neo4j_driver):
    """Test retrieving complete herb subgraph"""
    center_node = {"id": "123", "name": "RenShen", "status": "pending"}
    related_node = {"id": "456", "name": "Ginseng", "status": "pending"}

    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "h": center_node,
        "nodes": [center_node, related_node],
        "edges": []
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.get_herb_graph("RenShen")

    assert result["center"]["name"] == "RenShen"
    assert len(result["nodes"]) == 2
    assert result["center"] is not None


@pytest.mark.asyncio
async def test_verify_node(graph_service, mock_neo4j_driver):
    """Test verifying a node updates its status to VERIFIED"""
    node_id = str(uuid4())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "n": {
            "id": node_id,
            "name": "RenShen",
            "status": "verified",
            "verification_id": "vid-123",
            "verified_by": "user-456",
            "verified_at": "2024-01-01T00:00:00"
        }
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.verify_node(
        node_id=node_id,
        verification_id="vid-123",
        verifier_id="user-456",
        status=NodeStatus.VERIFIED.value
    )

    assert result["status"] == "verified"
    assert result["verification_id"] == "vid-123"
    assert result["verified_by"] == "user-456"


@pytest.mark.asyncio
async def test_verify_relationship(graph_service, mock_neo4j_driver):
    """Test verifying a relationship updates its status to VERIFIED"""
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "r": {
            "type": "父类",
            "status": "verified",
            "verification_id": "vid-789",
            "verified_by": "user-456",
            "verified_at": "2024-01-01T00:00:00"
        }
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await graph_service.verify_relationship(
        from_name="RenShen",
        rel_type="父类",
        to_name="Ginseng",
        verification_id="vid-789",
        verifier_id="user-456",
        status=NodeStatus.VERIFIED.value
    )

    assert result["status"] == "verified"
    assert result["verification_id"] == "vid-789"
    assert result["type"] == "父类"
