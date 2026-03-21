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
        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.get_herb_graph = AsyncMock(return_value=graph_data)

            resp = await client.get("/api/v1/graph/herb/ginseng")

        assert_status(resp, 200)
        assert_graph_response(resp.json())
        assert resp.json()["center"]["name"] == "ginseng"

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


class TestGetNode:
    """GET /api/v1/graph/node/{node_id}"""

    @pytest.mark.asyncio
    async def test_get_node_found(self, client):
        """GET existing node returns node data."""
        node_data = {"id": "node-abc", "name": "ginseng", "labels": ["Herb"]}
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
                "label": "Herb",
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
                            "labels": ["Herb"],
                        },
                        "target": {
                            "id": "eff-1",
                            "name": "补气",
                            "source": "本草纲目",
                            "status": "verified",
                            "labels": ["Efficacy"],
                        },
                    }
                ],
            },
        }

        with patch("app.api.graph.graph_service") as mock_svc:
            mock_svc.query_graph = AsyncMock(return_value=service_response)

            resp = await client.post("/api/v1/graph/query", json=payload)

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(data, {"summary", "graph"})
        assert data["graph"]["edges"][0]["rel_type"] == "HAS_EFFICACY"
        assert data["graph"]["edges"][0]["source"]["name"] == "人参"
        forwarded_payload = mock_svc.query_graph.await_args.args[0]
        assert forwarded_payload.node.label == NodeType.HERB
        assert forwarded_payload.node.status == NodeStatus.VERIFIED
        assert forwarded_payload.node.source_contains == "本草纲目"
        assert forwarded_payload.node.property_key == "latin_name"
        assert forwarded_payload.node.property_value_contains == "ginseng"
        assert forwarded_payload.edge.rel_type == EdgeType.HAS_EFFICACY
        assert forwarded_payload.edge.status == NodeStatus.VERIFIED
        assert forwarded_payload.edge.connected_name_contains == "补气"
