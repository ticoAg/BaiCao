"""Integration tests for Herb API routes (/api/v1/herbs/).

Tests mock HerbService to isolate route-level behavior.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from .helpers import assert_status, assert_pagination, make_herb


class TestGetHerb:
    """GET /api/v1/herbs/{herb_id}"""

    @pytest.mark.asyncio
    async def test_get_herb_found(self, client):
        """GET existing herb returns herb data."""
        herb = make_herb()
        with patch("app.api.herb.HerbService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_by_id = AsyncMock(return_value=herb)

            resp = await client.get(f"/api/v1/herbs/{herb.id}")

        assert_status(resp, 200)
        assert resp.json()["name"] == "ginseng"

    @pytest.mark.asyncio
    async def test_get_herb_not_found(self, client):
        """GET non-existent herb returns 404."""
        herb_id = uuid4()
        with patch("app.api.herb.HerbService") as MockSvc:
            instance = MockSvc.return_value
            instance.get_by_id = AsyncMock(return_value=None)

            resp = await client.get(f"/api/v1/herbs/{herb_id}")

        assert_status(resp, 404)


class TestListHerbs:
    """GET /api/v1/herbs/"""

    @pytest.mark.asyncio
    async def test_list_herbs_returns_paginated(self, client):
        """GET list returns paginated response structure."""
        herbs = [make_herb(name="ginseng"), make_herb(name="licorice")]
        with patch("app.api.herb.HerbService") as MockSvc:
            instance = MockSvc.return_value
            instance.list_herbs = AsyncMock(return_value=(herbs, 2))

            resp = await client.get("/api/v1/herbs/")

        assert_status(resp, 200)
        data = resp.json()
        assert_pagination(data)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["has_more"] is False
