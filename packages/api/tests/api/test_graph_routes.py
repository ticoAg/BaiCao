"""Integration tests for Graph API routes (/api/v1/graph/).

Tests mock the graph_service singleton to isolate route-level behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch

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
