from unittest.mock import AsyncMock, patch

import pytest


from app.core.config import get_settings


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
    from app.kg.db import build_neomodel_url, init_kg_db

    settings = get_settings()
    expected_url = build_neomodel_url(
        settings.neo4j_uri,
        settings.neo4j_user,
        settings.neo4j_password,
    )

    with patch("app.kg.db.adb.set_connection", new=AsyncMock()) as mock_set:
        await init_kg_db()

    mock_set.assert_awaited_once_with(expected_url)
