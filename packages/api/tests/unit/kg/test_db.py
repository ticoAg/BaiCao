from unittest.mock import AsyncMock, PropertyMock, patch

import pytest

def test_build_neomodel_url_includes_auth() -> None:
    from app.kg.db import build_neomodel_url

    assert (
        build_neomodel_url(
            "bolt://localhost:7687",
            "neo4j",
            "password",
        )
        == "bolt://neo4j:password@localhost:7687"
    )


@pytest.mark.asyncio
async def test_init_kg_db_calls_set_connection() -> None:
    from app.kg.db import get_expected_neomodel_url, init_kg_db

    expected_url = get_expected_neomodel_url()

    with patch("app.kg.db.adb.set_connection", new=AsyncMock()) as mock_set:
        await init_kg_db()

    mock_set.assert_awaited_once_with(expected_url)


@pytest.mark.asyncio
async def test_cypher_query_rebinds_when_adb_url_drifted() -> None:
    from app.kg.db import cypher_query, get_expected_neomodel_url
    from neomodel import adb

    expected_url = get_expected_neomodel_url()

    with (
        patch("app.kg.db.adb.set_connection", new=AsyncMock()) as mock_set,
        patch("app.kg.db.adb.cypher_query", new=AsyncMock(return_value=([], []))) as mock_query,
        patch.object(type(adb), "url", new_callable=PropertyMock, return_value="bolt://neo4j:password@localhost:9999"),
    ):
        rows, meta = await cypher_query("RETURN 1", {})

    assert rows == []
    assert meta == []
    mock_set.assert_awaited_once_with(expected_url)
    mock_query.assert_awaited_once_with("RETURN 1", {})
