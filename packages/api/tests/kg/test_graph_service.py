"""GraphService TDD - Neo4j Knowledge Graph Core Operations

RED phase: 10 test cases defining expected behavior for GraphService methods.
Each test uses a mocked Neo4j async driver to avoid external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Any, Dict, List, Optional

from app.models.enums import NodeStatus, HerbType


# ---------------------------------------------------------------------------
# Mock Neo4j helpers
# ---------------------------------------------------------------------------

class MockNeo4jRecord:
    """Simulates a neo4j.Record object with dict-like access."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def data(self) -> Dict[str, Any]:
        return dict(self._data)


class MockNeo4jNode:
    """Simulates a neo4j.graph.Node with dict() conversion."""

    def __init__(self, props: Dict[str, Any]) -> None:
        self._props = dict(props)

    def __iter__(self):
        return iter(self._props)

    def __getitem__(self, key: str) -> Any:
        return self._props[key]

    def keys(self):
        return self._props.keys()

    def values(self):
        return self._props.values()

    def items(self):
        return self._props.items()

    def get(self, key: str, default: Any = None) -> Any:
        return self._props.get(key, default)


class MockNeo4jRelationship:
    """Simulates a neo4j.graph.Relationship with dict() conversion."""

    def __init__(self, props: Dict[str, Any]) -> None:
        self._props = dict(props)

    def __iter__(self):
        return iter(self._props)

    def __getitem__(self, key: str) -> Any:
        return self._props[key]

    def keys(self):
        return self._props.keys()

    def values(self):
        return self._props.values()

    def items(self):
        return self._props.items()

    def get(self, key: str, default: Any = None) -> Any:
        return self._props.get(key, default)


def _make_result(record: Optional[MockNeo4jRecord] = None) -> AsyncMock:
    """Build an AsyncMock that behaves like a neo4j.Result."""
    result = AsyncMock()
    result.single = AsyncMock(return_value=record)
    result.data = AsyncMock(return_value=[record.data()] if record else [])
    return result


def _make_data_result(rows: List[Dict[str, Any]]) -> AsyncMock:
    """Build an AsyncMock neo4j.Result whose .data() returns *rows*."""
    result = AsyncMock()
    result.single = AsyncMock(return_value=None)
    result.data = AsyncMock(return_value=rows)
    return result


def _make_session(result: AsyncMock) -> AsyncMock:
    """Build an AsyncMock neo4j session that returns *result* on .run()."""
    session = AsyncMock()
    session.run = AsyncMock(return_value=result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


def _make_driver(session: AsyncMock) -> MagicMock:
    """Build a MagicMock neo4j driver whose .session() yields *session*."""
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    return driver


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def graph_service():
    """Return a fresh GraphService instance with a mocked driver."""
    from app.kg.graph_service import GraphService
    svc = GraphService()
    return svc


def _inject_driver(svc: Any, record: Optional[MockNeo4jRecord]) -> MagicMock:
    """Wire a mock driver -> session -> result -> record into *svc*."""
    result = _make_result(record)
    session = _make_session(result)
    driver = _make_driver(session)
    svc.driver = driver
    return driver


def _inject_data_driver(svc: Any, rows: List[Dict[str, Any]]) -> MagicMock:
    """Wire a mock driver whose result.data() returns *rows*."""
    result = _make_data_result(rows)
    session = _make_session(result)
    driver = _make_driver(session)
    svc.driver = driver
    return driver


# ---------------------------------------------------------------------------
# Test 1: test_create_node
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_create_node(graph_service):
    """create_node should return a dict with id, name, source, status=pending."""
    node_props = {
        "id": "test-id-123",
        "name": "TestHerb",
        "source": "test",
        "status": NodeStatus.PENDING.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)

    result = await graph_service.create_node("Herb", "TestHerb", "test")

    assert result["name"] == "TestHerb"
    assert result["source"] == "test"
    assert result["status"] == "pending"


# ---------------------------------------------------------------------------
# Test 2: test_get_node
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_get_node(graph_service):
    """get_node should return node dict with labels when found."""
    node_props = {
        "id": "node-456",
        "name": "SomeNode",
        "source": "import",
        "status": "pending",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node, "labels": ["Herb"]})
    _inject_driver(graph_service, record)

    result = await graph_service.get_node("node-456")

    assert result is not None
    assert result["id"] == "node-456"
    assert result["name"] == "SomeNode"
    assert result["labels"] == ["药材"]


# ---------------------------------------------------------------------------
# Test 3: test_get_node_not_found
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_get_node_not_found(graph_service):
    """get_node should return None when node does not exist."""
    _inject_driver(graph_service, None)

    result = await graph_service.get_node("nonexistent-id")

    assert result is None


# ---------------------------------------------------------------------------
# Test 4: test_create_herb
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_create_herb(graph_service):
    """create_herb should delegate to create_node with label 'Herb'."""
    herb_props = {
        "id": "herb-001",
        "name": "DangGui",
        "source": "ancient-text",
        "type": HerbType.BASE.value,
        "category": "BuXue",
        "status": NodeStatus.PENDING.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(herb_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)

    result = await graph_service.create_herb(
        name="DangGui",
        source="ancient-text",
        herb_type=HerbType.BASE,
        category="BuXue",
    )

    assert result["name"] == "DangGui"
    assert result["type"] == "base"
    assert result["category"] == "BuXue"
    assert result["status"] == "pending"


# ---------------------------------------------------------------------------
# Test 5: test_link_herb_parent
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_link_herb_parent(graph_service):
    """link_herb_parent should create 父类 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": NodeStatus.PENDING.value, "type": "父类"}
    )

    result = await graph_service.link_herb_parent(
        child_name="ShengDangGui",
        parent_name="DangGui",
    )

    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "ShengDangGui", "Herb", "DangGui", "父类"
    )


# ---------------------------------------------------------------------------
# Test 6: test_link_herb_child
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_link_herb_child(graph_service):
    """link_herb_child should create 子类 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": NodeStatus.PENDING.value, "type": "子类"}
    )

    result = await graph_service.link_herb_child(
        parent_name="DangGui",
        child_name="ShengDangGui",
    )

    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "DangGui", "Herb", "ShengDangGui", "子类"
    )


# ---------------------------------------------------------------------------
# Test 7: test_link_herb_source
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_link_herb_source(graph_service):
    """link_herb_source should create 来源于 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": NodeStatus.PENDING.value, "type": "来源于"}
    )

    result = await graph_service.link_herb_source(
        herb_name="DangGui",
        source_name="GanSu",
    )

    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "DangGui", "Source", "GanSu", "来源于"
    )


@pytest.mark.unit
async def test_graph_metadata_service_summary_aggregates_database_counts():
    from app.kg.graph_metadata_service import GraphMetadataService

    svc = GraphMetadataService()
    _inject_data_driver(
        svc,
        [
            {"result": {"name": "nodes", "data": 12}},
            {"result": {"name": "relationships", "data": 18}},
            {"result": {"name": "labels", "data": ["Herb", "Efficacy"]}},
            {"result": {"name": "relationshipTypes", "data": ["具有功效"]}},
            {"result": {"name": "propertyKeys", "data": ["name", "category"]}},
            {"result": {"name": "indexes", "data": [{"name": "idx_herb_name"}]}},
            {"result": {"name": "constraints", "data": [{"name": "constraint_herb_name"}]}},
        ],
    )

    summary = await svc.get_summary()

    assert summary["node_count"] == 12
    assert summary["relationship_count"] == 18
    assert summary["label_count"] == 2
    assert summary["property_key_count"] == 2
    assert summary["index_count"] == 1
    assert summary["constraint_count"] == 1


@pytest.mark.unit
async def test_graph_metadata_service_schema_normalizes_indexes_and_constraints():
    from app.kg.graph_metadata_service import GraphMetadataService

    svc = GraphMetadataService()
    indexes_result = _make_data_result(
        [
            {
                "name": "idx_herb_name",
                "type": "RANGE",
                "entityType": "NODE",
                "labelsOrTypes": ["Herb"],
                "properties": ["name"],
                "state": "ONLINE",
            }
        ]
    )
    constraints_result = _make_data_result(
        [
            {
                "name": "constraint_herb_name",
                "type": "UNIQUENESS",
                "entityType": "NODE",
                "labelsOrTypes": ["Herb"],
                "properties": ["name"],
            }
        ]
    )
    session = AsyncMock()
    session.run = AsyncMock(side_effect=[indexes_result, constraints_result])
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    svc.driver = _make_driver(session)

    schema = await svc.get_schema()

    assert schema["indexes"][0]["labels_or_types"] == ["药材"]
    assert schema["indexes"][0]["state"] == "ONLINE"
    assert schema["constraints"][0]["properties"] == ["name"]


# ---------------------------------------------------------------------------
# Test 8: test_get_herb_graph
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_get_herb_graph(graph_service):
    """get_herb_graph should return center, nodes, edges structure."""
    center_dict = {
        "id": "herb-001",
        "name": "DangGui",
        "source": "ancient-text",
        "status": "pending",
        "labels": ["Herb"],
    }
    connected_node = {
        "id": "comp-001",
        "name": "LiGusTiLiDe",
        "source": "research",
        "status": "pending",
        "labels": ["Component"],
    }
    edge_dict = {
        "id": "rel-001",
        "rel_type": "包含成分",
        "status": "pending",
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {
            "id": "herb-001",
            "name": "DangGui",
            "source": "ancient-text",
            "status": "pending",
            "labels": ["Herb"],
        },
        "target": {
            "id": "comp-001",
            "name": "LiGusTiLiDe",
            "source": "research",
            "status": "pending",
            "labels": ["Component"],
        },
    }

    record = MockNeo4jRecord({
        "center": center_dict,
        "nodes": [connected_node],
        "edges": [edge_dict],
    })
    _inject_driver(graph_service, record)

    result = await graph_service.get_herb_graph("DangGui")

    assert result["center"]["name"] == "DangGui"
    assert len(result["nodes"]) >= 1
    assert len(result["edges"]) == 1
    assert result["edges"][0]["rel_type"] == "包含成分"
    assert result["scene"] == {
        "truncated": False,
        "node_limit_hit": False,
        "relationship_limit_hit": False,
        "info_message": None,
    }


@pytest.mark.unit
async def test_get_herb_graph_limits_paths_before_aggregation(graph_service):
    graph_service._query_single = AsyncMock(return_value={
        "center": {"id": "herb-1", "name": "人参", "labels": ["药材"]},
        "nodes": [],
        "edges": [],
        "truncated": True,
    })

    result = await graph_service.get_herb_graph("人参", limit=12)

    query, params = graph_service._query_single.await_args.args
    assert "WITH h, path LIMIT $fetch_limit" in query
    assert params == {"name": "人参", "limit": 12, "fetch_limit": 13}
    assert result["scene"]["truncated"] is True
    assert result["scene"]["relationship_limit_hit"] is True


# ---------------------------------------------------------------------------
# Test 9: test_verify_node
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_verify_node(graph_service):
    """verify_node should update node status to verified."""
    verified_props = {
        "id": "node-789",
        "name": "DangGui",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": "ver-001",
        "verified_by": "expert-001",
        "verified_at": "2026-03-21T00:00:00Z",
    }
    returned_node = MockNeo4jNode(verified_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)

    result = await graph_service.verify_node(
        node_id="node-789",
        verification_id="ver-001",
        verifier_id="expert-001",
    )

    assert result is not None
    assert result["status"] == "verified"
    assert result["verification_id"] == "ver-001"
    assert result["verified_by"] == "expert-001"


# ---------------------------------------------------------------------------
# Test 10: test_verify_relationship
# ---------------------------------------------------------------------------

@pytest.mark.unit
async def test_verify_relationship(graph_service):
    """verify_relationship should update relationship status to verified."""
    verified_rel = {
        "status": NodeStatus.VERIFIED.value,
        "verification_id": "ver-002",
        "verified_by": "expert-001",
        "verified_at": "2026-03-21T00:00:00Z",
    }
    returned_rel = MockNeo4jRelationship(verified_rel)
    record = MockNeo4jRecord({"r": returned_rel})
    _inject_driver(graph_service, record)

    result = await graph_service.verify_relationship(
        from_name="DangGui",
        rel_type="包含成分",
        to_name="LiGusTiLiDe",
        verification_id="ver-002",
        verifier_id="expert-001",
    )

    assert result is not None
    assert result["status"] == "verified"
    assert result["verification_id"] == "ver-002"


@pytest.mark.unit
async def test_query_graph_filters_by_name_label_and_rel_type(graph_service):
    """query_graph should build a bounded label/type-filtered query and return graph data."""
    matched_node = {
        "id": "herb-001",
        "name": "人参",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Herb"],
    }
    connected_node = {
        "id": "eff-001",
        "name": "补气",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Efficacy"],
    }
    edge_dict = {
        "id": "rel-001",
        "rel_type": "具有功效",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {
            "id": "herb-001",
            "name": "人参",
            "source": "本草纲目",
            "status": NodeStatus.VERIFIED.value,
            "labels": ["Herb"],
        },
        "target": {
            "id": "eff-001",
            "name": "补气",
            "source": "本草纲目",
            "status": NodeStatus.VERIFIED.value,
            "labels": ["Efficacy"],
        },
    }

    seed_result = _make_data_result([{"node": matched_node}])
    expand_level_one = _make_data_result(
        [{"connected_node": connected_node, "edge": edge_dict}]
    )
    expand_level_two = _make_data_result([])
    session = AsyncMock()
    session.run = AsyncMock(side_effect=[seed_result, expand_level_one, expand_level_two])
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver

    result = await graph_service.query_graph(
        {
            "node": {"name_contains": "人参", "label": "Herb"},
            "edge": {"rel_type": "具有功效"},
            "depth": 2,
            "limit": 20,
        }
    )

    assert result["summary"]["mode"] == "advanced-query"
    assert result["summary"]["matched_nodes"] == 1
    assert result["summary"]["matched_edges"] == 1
    assert result["summary"]["active_filters"] == ["名称包含: 人参", "节点类型: 药材", "关系类型: 具有功效"]
    assert result["graph"]["center"] is None
    assert result["graph"]["nodes"][0]["name"] == "人参"
    assert result["graph"]["edges"][0]["rel_type"] == "具有功效"
    assert result["scene"] == {
        "truncated": False,
        "node_limit_hit": False,
        "relationship_limit_hit": False,
        "info_message": None,
    }

    first_query = session.run.await_args_list[0].args[0]
    first_params = session.run.await_args_list[0].kwargs
    second_query = session.run.await_args_list[1].args[0]
    second_params = session.run.await_args_list[1].kwargs
    third_params = session.run.await_args_list[2].kwargs
    assert "MATCH (n:药材)" in first_query
    assert "具有功效" in first_query
    assert "n.名称 CONTAINS $name_contains" in first_query
    assert first_params["name_contains"] == "人参"
    assert "[*1.." not in first_query
    assert "[*1.." not in second_query
    assert "current.标识 IN $frontier_ids" in second_query
    assert "current.id IN $frontier_ids" not in second_query
    assert second_params["frontier_ids"] == ["herb-001"]
    assert third_params["frontier_ids"] == ["eff-001"]
    assert session.run.await_count == 3


@pytest.mark.unit
async def test_query_graph_returns_empty_graph_when_no_match(graph_service):
    """query_graph should return an empty graph instead of raising when nothing matches."""
    seed_result = _make_data_result([])
    session = AsyncMock()
    session.run = AsyncMock(return_value=seed_result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver

    result = await graph_service.query_graph(
        {"node": {"name_contains": "不存在"}, "edge": {}, "depth": 1, "limit": 10}
    )

    assert result["summary"]["mode"] == "advanced-query"
    assert result["summary"]["matched_nodes"] == 0
    assert result["summary"]["matched_edges"] == 0
    assert result["summary"]["active_filters"] == ["名称包含: 不存在"]
    assert result["graph"]["center"] is None
    assert result["graph"]["nodes"] == []
    assert result["graph"]["edges"] == []
    assert result["scene"]["truncated"] is False
    assert session.run.await_count == 1


@pytest.mark.unit
async def test_query_graph_filters_out_non_matching_edges_during_expansion(graph_service):
    """query_graph should not mix non-matching relationships into the returned graph."""
    matched_node = {
        "id": "herb-001",
        "name": "人参",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Herb"],
    }
    efficacy_node = {
        "id": "eff-001",
        "name": "补气",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Efficacy"],
    }
    flavor_node = {
        "id": "flv-001",
        "name": "甘",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Flavor"],
    }
    efficacy_edge = {
        "id": "rel-001",
        "rel_type": "具有功效",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {
            "id": "herb-001",
            "name": "人参",
            "source": "本草纲目",
            "status": NodeStatus.VERIFIED.value,
            "labels": ["Herb"],
        },
        "target": {
            "id": "eff-001",
            "name": "补气",
            "source": "本草纲目",
            "status": NodeStatus.VERIFIED.value,
            "labels": ["Efficacy"],
        },
    }
    flavor_edge = {
        "id": "rel-002",
        "rel_type": "具有性味",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {
            "id": "herb-001",
            "name": "人参",
            "source": "本草纲目",
            "status": NodeStatus.VERIFIED.value,
            "labels": ["Herb"],
        },
        "target": {
            "id": "flv-001",
            "name": "甘",
            "source": "本草纲目",
            "status": NodeStatus.VERIFIED.value,
            "labels": ["Flavor"],
        },
    }

    seed_result = _make_data_result([{"node": matched_node}])
    expand_result = _make_data_result(
        [
            {"connected_node": efficacy_node, "edge": efficacy_edge},
            {"connected_node": flavor_node, "edge": flavor_edge},
        ]
    )
    session = AsyncMock()
    session.run = AsyncMock(side_effect=[seed_result, expand_result])
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver

    result = await graph_service.query_graph(
        {
            "node": {"name_contains": "人参", "label": "Herb"},
            "edge": {"rel_type": "具有功效"},
            "depth": 1,
            "limit": 20,
        }
    )

    assert [edge["rel_type"] for edge in result["graph"]["edges"]] == ["具有功效"]
    assert [node["name"] for node in result["graph"]["nodes"]] == ["人参", "补气"]
    assert result["summary"]["matched_edges"] == 1
    assert result["scene"]["relationship_limit_hit"] is False


@pytest.mark.unit
async def test_query_graph_applies_remaining_budget_to_expansion(graph_service):
    """query_graph should tighten per-hop expansion budget as graph budget is consumed."""
    matched_node = {
        "id": "herb-001",
        "name": "人参",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Herb"],
    }
    efficacy_node = {
        "id": "eff-001",
        "name": "补气",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Efficacy"],
    }
    flavor_node = {
        "id": "flv-001",
        "name": "甘",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Flavor"],
    }
    disease_node = {
        "id": "dis-001",
        "name": "虚证",
        "source": "本草纲目",
        "status": NodeStatus.VERIFIED.value,
        "labels": ["Disease"],
    }
    efficacy_edge = {
        "id": "rel-001",
        "rel_type": "具有功效",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {"id": "herb-001", "name": "人参", "source": "本草纲目", "status": "verified", "labels": ["Herb"]},
        "target": {"id": "eff-001", "name": "补气", "source": "本草纲目", "status": "verified", "labels": ["Efficacy"]},
    }
    flavor_edge = {
        "id": "rel-002",
        "rel_type": "具有性味",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {"id": "herb-001", "name": "人参", "source": "本草纲目", "status": "verified", "labels": ["Herb"]},
        "target": {"id": "flv-001", "name": "甘", "source": "本草纲目", "status": "verified", "labels": ["Flavor"]},
    }
    treats_edge = {
        "id": "rel-003",
        "rel_type": "治疗病证",
        "status": NodeStatus.VERIFIED.value,
        "verification_id": None,
        "verified_by": None,
        "verified_at": None,
        "source": {"id": "eff-001", "name": "补气", "source": "本草纲目", "status": "verified", "labels": ["Efficacy"]},
        "target": {"id": "dis-001", "name": "虚证", "source": "本草纲目", "status": "verified", "labels": ["Disease"]},
    }

    seed_result = _make_data_result([{"node": matched_node}])
    expand_level_one = _make_data_result(
        [
            {"connected_node": efficacy_node, "edge": efficacy_edge},
            {"connected_node": flavor_node, "edge": flavor_edge},
        ]
    )
    expand_level_two = _make_data_result(
        [{"connected_node": disease_node, "edge": treats_edge}]
    )
    session = AsyncMock()
    session.run = AsyncMock(side_effect=[seed_result, expand_level_one, expand_level_two])
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver

    result = await graph_service.query_graph(
        {
            "node": {"name_contains": "人参", "label": "Herb"},
            "edge": {},
            "depth": 2,
            "limit": 1,
        }
    )

    second_params = session.run.await_args_list[1].kwargs
    assert second_params["hop_limit"] == 1
    assert result["summary"]["matched_edges"] == 1
    assert len(result["graph"]["nodes"]) == 2
    assert len(result["graph"]["edges"]) == 1
    assert result["scene"]["node_limit_hit"] is False


# ===========================================================================
# Supplementary tests for coverage (utility methods, edge cases, other ops)
# ===========================================================================

@pytest.mark.unit
async def test_graph_service_starts_without_local_driver(graph_service):
    """runtime should not create a local Neo4j driver by default."""
    assert graph_service.driver is None


@pytest.mark.unit
async def test_query_rows_uses_injected_driver_when_present(graph_service):
    """tests may still inject a mock driver seam for isolated execution."""
    result = _make_data_result([{"n": {"id": "node-1"}}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    graph_service.driver = MagicMock(session=MagicMock(return_value=session))

    rows = await graph_service._query_rows("RETURN n")

    assert rows == [{"n": {"id": "node-1"}}]
    session.run.assert_awaited_once_with("RETURN n")


@pytest.mark.unit
async def test_query_single_uses_injected_driver_when_present(graph_service):
    """single-record helper should also honor injected mock driver."""
    record = MockNeo4jRecord({"n": {"id": "node-1"}})
    result = _make_result(record)
    session = AsyncMock()
    session.run = AsyncMock(return_value=result)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    graph_service.driver = MagicMock(session=MagicMock(return_value=session))

    row = await graph_service._query_single("RETURN n")

    assert row["n"]["id"] == "node-1"


@pytest.mark.unit
def test_record_value_key_error(graph_service):
    """_record_value should return None on KeyError."""
    assert graph_service._record_value({}, "missing") is None


@pytest.mark.unit
def test_record_value_type_error(graph_service):
    """_record_value should return None on TypeError."""
    assert graph_service._record_value(None, "any") is None


@pytest.mark.unit
def test_dedupe_nodes_skips_none(graph_service):
    """_dedupe_nodes should skip None entries."""
    nodes = [None, {"id": "1", "name": "A"}, None, {"id": "1", "name": "A"}]
    result = graph_service._dedupe_nodes(nodes)
    assert len(result) == 1


@pytest.mark.unit
def test_dedupe_edges_skips_none(graph_service):
    """_dedupe_edges should skip None entries."""
    edges = [
        None,
        {"source": {"id": "1"}, "target": {"id": "2"}, "rel_type": "X"},
        {"source": {"id": "1"}, "target": {"id": "2"}, "rel_type": "X"},
    ]
    result = graph_service._dedupe_edges(edges)
    assert len(result) == 1


@pytest.mark.unit
def test_map_relationship_to_dict(graph_service):
    """_map_relationship_to_dict should return dict from relationship."""
    rel = MockNeo4jRelationship({"status": "pending", "extra": "val"})
    result = graph_service._map_relationship_to_dict(rel)
    assert result["status"] == "pending"
    assert result["extra"] == "val"


@pytest.mark.unit
async def test_get_node_by_name(graph_service):
    """get_node_by_name should find a node by label and name."""
    node_props = {"id": "n-1", "name": "DangGui", "status": "pending"}
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node, "labels": ["Herb"]})
    _inject_driver(graph_service, record)
    result = await graph_service.get_node_by_name("DangGui", "Herb")
    assert result is not None
    assert result["name"] == "DangGui"
    assert result["labels"] == ["药材"]


@pytest.mark.unit
async def test_get_herb(graph_service):
    """get_herb should delegate to get_node_by_name with Herb label."""
    node_props = {"id": "n-2", "name": "RenShen", "status": "pending"}
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node, "labels": ["Herb"]})
    _inject_driver(graph_service, record)
    result = await graph_service.get_herb("RenShen")
    assert result is not None
    assert result["name"] == "RenShen"


@pytest.mark.unit
async def test_create_component(graph_service):
    """create_component should create a Component node."""
    node_props = {
        "id": "comp-001", "name": "Berberine", "source": "research",
        "chemical_formula": "C20H18NO4", "status": "pending",
        "verification_id": None, "verified_by": None, "verified_at": None,
        "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_component("Berberine", "research", "C20H18NO4")
    assert result["name"] == "Berberine"
    assert result["chemical_formula"] == "C20H18NO4"


@pytest.mark.unit
async def test_link_herb_contains_component(graph_service):
    """link_herb_contains_component should create 包含成分 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": "pending", "quantity": "5%", "type": "包含成分"}
    )
    result = await graph_service.link_herb_contains_component("HuangLian", "Berberine", "5%")
    assert result["status"] == "pending"
    assert result["quantity"] == "5%"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "HuangLian", "Component", "Berberine", "包含成分", {"quantity": "5%"}
    )


@pytest.mark.unit
async def test_create_variant(graph_service):
    """create_variant should create Variant node and link to parent herb."""
    node_props = {
        "id": "var-001", "name": "ChuanDangGui", "source": "import",
        "parent_herb": "DangGui", "description": "Sichuan variant",
        "status": "pending", "verification_id": None, "verified_by": None,
        "verified_at": None, "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    result_create = _make_result(record)
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_create)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    graph_service.link_variant_of = AsyncMock(return_value={"status": "pending"})

    result = await graph_service.create_variant("ChuanDangGui", "DangGui", "import", "Sichuan variant")
    assert result["name"] == "ChuanDangGui"
    graph_service.link_variant_of.assert_awaited_once_with("ChuanDangGui", "DangGui")
    assert result["parent_herb"] == "DangGui"


@pytest.mark.unit
async def test_create_process(graph_service):
    """create_process should create a Process node."""
    node_props = {
        "id": "proc-001", "name": "PaoZhi", "source": "traditional",
        "description": "Traditional processing", "min_duration": "2h", "conditions": "low heat",
        "status": "pending", "verification_id": None, "verified_by": None,
        "verified_at": None, "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_process("PaoZhi", "traditional", "Traditional processing", "2h", "low heat")
    assert result["name"] == "PaoZhi"


@pytest.mark.unit
async def test_link_herb_processed_by(graph_service):
    """link_herb_processed_by should create 经过工艺 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={
            "status": "pending",
            "duration": "3h",
            "conditions": "medium heat",
            "type": "经过工艺",
        }
    )
    result = await graph_service.link_herb_processed_by("DangGui", "PaoZhi", "3h", "medium heat")
    assert result["status"] == "pending"
    assert result["duration"] == "3h"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb",
        "DangGui",
        "Process",
        "PaoZhi",
        "经过工艺",
        {"duration": "3h", "conditions": "medium heat", "start_date": None, "end_date": None},
    )


@pytest.mark.unit
async def test_create_trait(graph_service):
    """create_trait should create a Trait node."""
    node_props = {
        "id": "trait-001", "name": "Color", "source": "observation",
        "category": "external", "description": "Visual color",
        "status": "pending", "verification_id": None, "verified_by": None,
        "verified_at": None, "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_trait("Color", "observation", description="Visual color")
    assert result["name"] == "Color"
    assert result["category"] == "external"


@pytest.mark.unit
async def test_link_herb_has_trait(graph_service):
    """link_herb_has_trait should create 具有性状 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": "pending", "value": "dark-brown", "type": "具有性状"}
    )
    result = await graph_service.link_herb_has_trait("DangGui", "Color", "dark-brown", "visual", "2020-2025")
    assert result["value"] == "dark-brown"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb",
        "DangGui",
        "Trait",
        "Color",
        "具有性状",
        {"value": "dark-brown", "observation": "visual", "year_range": "2020-2025"},
    )


@pytest.mark.unit
async def test_create_efficacy(graph_service):
    """create_efficacy should create Efficacy node."""
    node_props = {
        "id": "eff-001", "name": "BuXue", "source": "classic",
        "category": "blood", "status": "pending",
        "verification_id": None, "verified_by": None, "verified_at": None,
        "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_efficacy("BuXue", "classic", "blood")
    assert result["name"] == "BuXue"


@pytest.mark.unit
async def test_create_flavor(graph_service):
    """create_flavor should create Flavor node."""
    node_props = {
        "id": "flv-001", "name": "Gan", "source": "classic",
        "nature": "warm", "status": "pending",
        "verification_id": None, "verified_by": None, "verified_at": None,
        "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_flavor("Gan", "classic", "warm")
    assert result["name"] == "Gan"


@pytest.mark.unit
async def test_create_meridian(graph_service):
    """create_meridian should create Meridian node."""
    node_props = {
        "id": "mer-001", "name": "Liver", "source": "classic",
        "status": "pending", "verification_id": None, "verified_by": None,
        "verified_at": None, "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_meridian("Liver", "classic")
    assert result["name"] == "Liver"


@pytest.mark.unit
async def test_link_herb_has_efficacy(graph_service):
    """link_herb_has_efficacy should create 具有功效 relationship."""
    graph_service.create_relationship = AsyncMock(return_value={"status": "pending", "type": "具有功效"})
    result = await graph_service.link_herb_has_efficacy("DangGui", "BuXue")
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "DangGui", "Efficacy", "BuXue", "具有功效"
    )


@pytest.mark.unit
async def test_link_herb_has_flavor(graph_service):
    """link_herb_has_flavor should create 具有性味 relationship."""
    graph_service.create_relationship = AsyncMock(return_value={"status": "pending", "type": "具有性味"})
    result = await graph_service.link_herb_has_flavor("DangGui", "Gan")
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "DangGui", "Flavor", "Gan", "具有性味"
    )


@pytest.mark.unit
async def test_link_herb_enters_meridian(graph_service):
    """link_herb_enters_meridian should create 归于经脉 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": "pending", "type": "归于经脉"}
    )
    result = await graph_service.link_herb_enters_meridian("DangGui", "Liver")
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "DangGui", "Meridian", "Liver", "归于经脉"
    )


@pytest.mark.unit
async def test_search_nodes_with_label(graph_service):
    """search_nodes should filter by label when provided."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"n": {"id": "n1", "name": "DangGui"}, "labels": ["Herb"]}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver

    result = await graph_service.search_nodes("Dang", label="药材", limit=10)
    assert len(result) == 1
    assert result[0]["node"]["name"] == "DangGui"
    assert result[0]["labels"] == ["药材"]


@pytest.mark.unit
async def test_search_nodes_without_label(graph_service):
    """search_nodes should search all nodes when no label provided."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"n": {"id": "n1", "name": "DangGui"}, "labels": ["Herb"]}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver

    result = await graph_service.search_nodes("Dang")
    assert len(result) == 1
    assert result[0]["labels"] == ["药材"]
    query = session.run.await_args.args[0] if session.run.await_args else ""
    assert "n.标识 = $search_text" in query
    assert "n.名称 CONTAINS $search_text" in query


@pytest.mark.unit
async def test_expand_node_graph_allows_two_hop_depth(graph_service):
    graph_service._query_single = AsyncMock(  # noqa: SLF001
        return_value={"n": {"标识": "药材:乌梅", "名称": "乌梅"}, "labels": ["药材"]}
    )
    graph_service._expand_query_subgraph = AsyncMock(return_value=([], []))  # noqa: SLF001

    await graph_service.expand_node_graph("药材:乌梅", depth=2, limit=20)

    called = graph_service._expand_query_subgraph.await_args  # noqa: SLF001
    assert called is not None
    assert called.args[2] == 2



@pytest.mark.unit
async def test_get_herb_graph_not_found(graph_service):
    """get_herb_graph should return empty when herb not found."""
    record = MockNeo4jRecord({"center": None, "nodes": [], "edges": []})
    _inject_driver(graph_service, record)
    result = await graph_service.get_herb_graph("NonExistent")
    assert result["center"] is None
    assert result["nodes"] == []
    assert result["edges"] == []


@pytest.mark.unit
async def test_get_herb_graph_no_record(graph_service):
    """get_herb_graph should return empty when no record returned."""
    _inject_driver(graph_service, None)
    result = await graph_service.get_herb_graph("NonExistent")
    assert result["center"] is None
    assert result["nodes"] == []


@pytest.mark.unit
async def test_verify_node_not_found(graph_service):
    """verify_node should return None when node not found."""
    _inject_driver(graph_service, None)
    result = await graph_service.verify_node("bad-id", "ver-x", "usr-x")
    assert result is None


@pytest.mark.unit
async def test_verify_relationship_not_found(graph_service):
    """verify_relationship should return None when relationship not found."""
    _inject_driver(graph_service, None)
    result = await graph_service.verify_relationship("A", "REL", "B", "ver-x", "usr-x")
    assert result is None


@pytest.mark.unit
async def test_get_pending_nodes_with_label(graph_service):
    """get_pending_nodes should filter by label."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"n": {"id": "n1", "name": "H1", "status": "pending"}, "labels": ["Herb"]}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_pending_nodes(label="药材")
    assert len(result) == 1
    assert result[0]["node"]["status"] == "pending"
    assert result[0]["labels"] == ["药材"]


@pytest.mark.unit
async def test_get_pending_nodes_without_label(graph_service):
    """get_pending_nodes without label should return all pending."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_pending_nodes()
    assert result == []


@pytest.mark.unit
async def test_get_pending_relationships(graph_service):
    """get_pending_relationships should return pending relationships."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"r": {"status": "pending"}}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_pending_relationships()
    assert len(result) == 1
    assert result[0]["status"] == "pending"


@pytest.mark.unit
async def test_find_path(graph_service):
    """find_path should return paths between two nodes."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"path": [{"id": "1", "name": "A"}, {"id": "2", "name": "B"}]}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.find_path("A", "B")
    assert len(result) == 1


@pytest.mark.unit
async def test_get_herb_components(graph_service):
    """get_herb_components should return list of components."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"c": {"name": "Berberine"}, "quantity": "5%", "status": "pending"}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_herb_components("HuangLian")
    assert len(result) == 1
    assert result[0]["component"]["name"] == "Berberine"


@pytest.mark.unit
async def test_get_herb_variants(graph_service):
    """get_herb_variants should return list of variants."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[{"v": {"name": "ChuanDangGui"}, "status": "pending"}])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_herb_variants("DangGui")
    assert len(result) == 1
    assert result[0]["variant"]["name"] == "ChuanDangGui"


@pytest.mark.unit
async def test_get_herb_traits_with_year_range(graph_service):
    """get_herb_traits should filter by year_range when provided."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[
        {"t": {"name": "Color"}, "value": "brown", "observation": "visual", "year_range": "2020-2025", "status": "pending"}
    ])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_herb_traits("DangGui", year_range="2020")
    assert len(result) == 1
    assert result[0]["value"] == "brown"


@pytest.mark.unit
async def test_get_herb_traits_without_year_range(graph_service):
    """get_herb_traits should return all traits when no year_range."""
    result_mock = AsyncMock()
    result_mock.data = AsyncMock(return_value=[])
    session = AsyncMock()
    session.run = AsyncMock(return_value=result_mock)
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    driver = MagicMock()
    driver.session = MagicMock(return_value=session)
    graph_service.driver = driver
    result = await graph_service.get_herb_traits("DangGui")
    assert result == []


@pytest.mark.unit
async def test_get_variant_details(graph_service):
    """get_variant_details should return variant with base_herb and traits."""
    record = MockNeo4jRecord({
        "v": MockNeo4jNode({"name": "ChuanDangGui"}),
        "base_herb": "DangGui",
        "traits": [],
        "efficacies": ["BuXue"],
    })
    _inject_driver(graph_service, record)
    result = await graph_service.get_variant_details("ChuanDangGui")
    assert result["base_herb"] == "DangGui"
    assert result["efficacies"] == ["BuXue"]


@pytest.mark.unit
async def test_get_variant_details_not_found(graph_service):
    """get_variant_details should return empty dict when not found."""
    _inject_driver(graph_service, None)
    result = await graph_service.get_variant_details("NonExistent")
    assert result == {}


@pytest.mark.unit
async def test_link_herb_has_variant(graph_service):
    """link_herb_has_variant should create 具有品种 relationship."""
    graph_service.create_relationship = AsyncMock(
        return_value={"status": "pending", "type": "具有品种"}
    )
    result = await graph_service.link_herb_has_variant("DangGui", "ChuanDangGui")
    assert result["status"] == "pending"
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb", "DangGui", "Variant", "ChuanDangGui", "具有品种"
    )


@pytest.mark.unit
async def test_create_timepoint(graph_service):
    """create_timepoint should create a TimePoint node."""
    node_props = {
        "id": "tp-001", "name": "5nian", "source": "system",
        "years": 5, "description": None, "quality_indicator": None,
        "status": "pending", "verification_id": None, "verified_by": None,
        "verified_at": None, "imported_at": "datetime()",
    }
    returned_node = MockNeo4jNode(node_props)
    record = MockNeo4jRecord({"n": returned_node})
    _inject_driver(graph_service, record)
    result = await graph_service.create_timepoint(5, "system")
    assert result["years"] == 5


@pytest.mark.unit
async def test_link_herb_stored_for(graph_service):
    """link_herb_stored_for should create 储存时间 relationship."""
    graph_service.create_timepoint = AsyncMock(return_value={"years": 3})
    graph_service.create_relationship = AsyncMock(
        return_value={"status": "pending", "years": 3, "type": "储存时间"}
    )

    result = await graph_service.link_herb_stored_for("DangGui", 3)
    assert result["status"] == "pending"
    assert result["years"] == 3
    graph_service.create_timepoint.assert_awaited_once_with(3, "system")
    graph_service.create_relationship.assert_awaited_once_with(
        "Herb",
        "DangGui",
        "TimePoint",
        "3年",
        "储存时间",
        {"years": 3, "start_date": None, "end_date": None},
    )
