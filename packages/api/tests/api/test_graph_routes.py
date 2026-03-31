"""Integration tests for Graph API routes (/api/v1/graph/).

Tests mock the graph_service singleton to isolate route-level behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.models.enums import EdgeType, NodeStatus, NodeType

from .helpers import (
    assert_status,
    assert_json_keys,
    assert_graph_response,
    assert_list_response,
    make_herb_graph,
    make_search_results,
)


class TestGetHerbGraph:
    """GET /api/v1/graph/herb/{name}"""

    @pytest.mark.asyncio
    async def test_get_herb_graph_found(self, client):
        """GET existing herb returns graph data."""
        graph_data = make_herb_graph("ginseng")
        graph_data["scene"] = {
            "truncated": False,
            "node_limit_hit": False,
            "relationship_limit_hit": False,
            "info_message": None,
        }
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.get_herb_graph = AsyncMock(return_value=graph_data)

            resp = await client.get("/api/v1/graph/herb/ginseng")

        assert_status(resp, 200)
        assert_graph_response(resp.json())
        assert resp.json()["center"]["name"] == "ginseng"
        assert_json_keys(
            resp.json()["scene"],
            {"truncated", "node_limit_hit", "relationship_limit_hit", "info_message"},
        )

    @pytest.mark.asyncio
    async def test_get_herb_graph_not_found(self, client):
        """GET non-existent herb returns 404."""
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.get_herb_graph = AsyncMock(
                return_value={"center": None, "nodes": [], "edges": []}
            )

            resp = await client.get("/api/v1/graph/herb/unknown")

        assert_status(resp, 404)


class TestSearchNodes:
    """GET /api/v1/graph/search"""

    @pytest.mark.asyncio
    async def test_search_nodes(self, client):
        """Search returns items and total."""
        results = make_search_results()
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.search_nodes = AsyncMock(return_value=results)

            resp = await client.get("/api/v1/graph/search", params={"q": "gin"})

        assert_status(resp, 200)
        assert_list_response(resp.json(), min_items=2)


class TestGraphMetadataRoutes:
    """GET /api/v1/graph/meta/*"""

    @pytest.mark.asyncio
    async def test_get_graph_meta_summary(self, client):
        """Summary endpoint returns database-level counts."""
        summary = {
            "node_count": 12,
            "relationship_count": 18,
            "label_count": 4,
            "relationship_type_count": 6,
            "property_key_count": 11,
            "index_count": 2,
            "constraint_count": 1,
            "truncated": False,
            "generated_at": "2026-03-23T10:00:00Z",
        }

        with patch("app.api.graph.graph_metadata_service") as mock_meta:
            mock_meta.get_summary = AsyncMock(return_value=summary)

            resp = await client.get("/api/v1/graph/meta/summary")

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(
            data,
            {
                "node_count",
                "relationship_count",
                "label_count",
                "relationship_type_count",
                "property_key_count",
                "index_count",
                "constraint_count",
                "truncated",
                "generated_at",
            },
        )

    @pytest.mark.asyncio
    async def test_get_graph_meta_labels_supports_limit(self, client):
        """Labels endpoint returns paginated metadata list."""
        labels = {
            "items": [
                {"name": "药材", "count": 3, "property_keys": ["name", "category"]},
                {"name": "功效", "count": 2, "property_keys": ["name"]},
            ],
            "total": 2,
        }

        with patch("app.api.graph.graph_metadata_service") as mock_meta:
            mock_meta.list_labels = AsyncMock(return_value=labels)

            resp = await client.get("/api/v1/graph/meta/labels", params={"limit": 20})

        assert_status(resp, 200)
        assert_list_response(resp.json(), min_items=2)
        mock_meta.list_labels.assert_awaited_once_with(q=None, limit=20, offset=0)

    @pytest.mark.asyncio
    async def test_get_graph_meta_schema_returns_indexes_and_constraints(self, client):
        """Schema endpoint returns indexes and constraints."""
        schema = {
            "indexes": [
                {
                    "name": "idx_herb_name",
                    "type": "RANGE",
                    "entity_type": "NODE",
                    "labels_or_types": ["药材"],
                    "properties": ["name"],
                    "state": "ONLINE",
                }
            ],
            "constraints": [
                {
                    "name": "constraint_herb_name",
                    "type": "UNIQUENESS",
                    "entity_type": "NODE",
                    "labels_or_types": ["药材"],
                    "properties": ["name"],
                }
            ],
        }

        with patch("app.api.graph.graph_metadata_service") as mock_meta:
            mock_meta.get_schema = AsyncMock(return_value=schema)

            resp = await client.get("/api/v1/graph/meta/schema")

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(data, {"indexes", "constraints"})
        assert data["indexes"][0]["labels_or_types"] == ["药材"]
        assert data["constraints"][0]["properties"] == ["name"]


class TestGetNode:
    """GET /api/v1/graph/node/{node_id}"""

    @pytest.mark.asyncio
    async def test_get_node_found(self, client):
        """GET existing node returns node data."""
        node_data = {"id": "node-abc", "name": "ginseng", "labels": ["药材"]}
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.get_node = AsyncMock(return_value=node_data)

            resp = await client.get("/api/v1/graph/node/node-abc")

        assert_status(resp, 200)
        assert resp.json()["id"] == "node-abc"

    @pytest.mark.asyncio
    async def test_get_node_not_found(self, client):
        """GET non-existent node returns 404."""
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.get_node = AsyncMock(return_value=None)

            resp = await client.get("/api/v1/graph/node/no-such-id")

        assert_status(resp, 404)


class TestExpandNodeGraph:
    """GET /api/v1/graph/node/{node_id}/expand"""

    @pytest.mark.asyncio
    async def test_expand_node_graph_returns_one_hop_subgraph(self, client):
        """Double-click expansion endpoint returns graph payload for one-hop neighbors."""
        graph_data = {
            "center": {
                "id": "node-abc",
                "name": "人参",
                "labels": ["药材"],
                "status": "verified",
            },
            "nodes": [
                {
                    "id": "node-abc",
                    "name": "人参",
                    "labels": ["药材"],
                    "status": "verified",
                },
                {
                    "id": "eff-1",
                    "name": "补气",
                    "labels": ["功效"],
                    "status": "verified",
                },
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "rel_type": "HAS_EFFICACY",
                    "status": "verified",
                    "verification_id": None,
                    "verified_by": None,
                    "verified_at": None,
                    "source": {
                        "id": "node-abc",
                        "name": "人参",
                        "source": "中国药典",
                        "status": "verified",
                        "labels": ["药材"],
                    },
                    "target": {
                        "id": "eff-1",
                        "name": "补气",
                        "source": "中国药典",
                        "status": "verified",
                        "labels": ["功效"],
                    },
                }
            ],
        }
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.expand_node_graph = AsyncMock(return_value=graph_data)

            resp = await client.get(
                "/api/v1/graph/node/node-abc/expand",
                params={"depth": 1, "limit": 20},
            )

        assert_status(resp, 200)
        assert_graph_response(resp.json())
        assert resp.json()["center"]["id"] == "node-abc"
        mock_svc.expand_node_graph.assert_awaited_once_with("node-abc", depth=1, limit=20)


class TestGetPending:
    """GET /api/v1/graph/pending"""

    @pytest.mark.asyncio
    async def test_get_pending_nodes(self, client):
        """GET pending nodes returns items list."""
        pending = [{"node": {"id": "p1"}, "labels": ["Herb"]}]
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.get_pending_nodes = AsyncMock(return_value=pending)

            resp = await client.get(
                "/api/v1/graph/pending", params={"type": "nodes"}
            )

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(data, {"items", "type"})
        assert data["type"] == "nodes"
        assert len(data["items"]) == 1


class TestGraphQuery:
    """POST /api/v1/graph/query"""

    @pytest.mark.asyncio
    async def test_query_graph_returns_summary_and_graph(self, client):
        """Advanced graph query returns summary and graph payload."""
        payload = {
            "node": {
                "name_contains": "人参",
                "label": "药材",
                "status": "verified",
                "source_contains": "本草纲目",
                "property_key": "latin_name",
                "property_value_contains": "ginseng",
            },
            "edge": {
                "rel_type": "HAS_EFFICACY",
                "status": "verified",
                "connected_name_contains": "补气",
            },
            "depth": 2,
            "limit": 20,
        }
        service_response = {
            "summary": {
                "mode": "advanced-query",
                "matched_nodes": 3,
                "matched_edges": 2,
                "truncated": False,
                "active_filters": ["名称包含: 人参", "关系类型: HAS_EFFICACY"],
            },
            "graph": {
                "center": None,
                "nodes": [],
                "edges": [
                    {
                        "id": "rel-1",
                        "rel_type": "HAS_EFFICACY",
                        "status": "verified",
                        "verification_id": None,
                        "verified_by": None,
                        "verified_at": None,
                        "source": {
                            "id": "herb-1",
                            "name": "人参",
                            "source": "本草纲目",
                            "status": "verified",
                            "labels": ["药材"],
                        },
                        "target": {
                            "id": "eff-1",
                            "name": "补气",
                            "source": "本草纲目",
                            "status": "verified",
                            "labels": ["功效"],
                        },
                    }
                ],
            },
            "scene": {
                "truncated": False,
                "node_limit_hit": False,
                "relationship_limit_hit": False,
                "info_message": None,
            },
        }

        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.query_graph = AsyncMock(return_value=service_response)

            resp = await client.post("/api/v1/graph/query", json=payload)

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(data, {"summary", "graph", "scene"})
        assert data["graph"]["edges"][0]["rel_type"] == "HAS_EFFICACY"
        assert data["graph"]["edges"][0]["source"]["name"] == "人参"
        assert_json_keys(
            data["scene"],
            {"truncated", "node_limit_hit", "relationship_limit_hit", "info_message"},
        )
        assert mock_svc.query_graph.await_args is not None
        forwarded_payload = mock_svc.query_graph.await_args.args[0]
        assert forwarded_payload.node.label == NodeType.HERB
        assert forwarded_payload.node.status == NodeStatus.VERIFIED
        assert forwarded_payload.node.source_contains == "本草纲目"
        assert forwarded_payload.node.property_key == "latin_name"
        assert forwarded_payload.node.property_value_contains == "ginseng"
        assert forwarded_payload.edge.rel_type == EdgeType.HAS_EFFICACY
        assert forwarded_payload.edge.status == NodeStatus.VERIFIED
        assert forwarded_payload.edge.connected_name_contains == "补气"

    @pytest.mark.asyncio
    async def test_query_graph_rejects_invalid_filter_enum(self, client):
        """Invalid enum or property_key values should be rejected by request schema."""
        payload = {
            "node": {
                "label": "NotALabel",
                "property_key": "drop_table",
            },
            "edge": {
                "rel_type": "NOT_A_REL",
            },
            "depth": 1,
            "limit": 10,
        }

        resp = await client.post("/api/v1/graph/query", json=payload)

        assert_status(resp, 422)
