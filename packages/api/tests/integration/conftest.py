# ruff: noqa: E402

import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from neo4j import AsyncGraphDatabase


REPO_ROOT = Path(__file__).resolve().parents[4]
API_DIR = REPO_ROOT / "packages" / "api"

for path in (REPO_ROOT, API_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, engine
from app.kg.graph_service import graph_service
from app.main import app
from scripts.seed_demo_data import DATASET_TAG, HERBS, SOURCES, USERS, seed_neo4j, seed_postgres


@pytest.fixture(scope="session")
def demo_seed_data() -> dict[str, object]:
    return {
        "dataset_tag": DATASET_TAG,
        "herb_ids": {item["name"]: str(item["id"]) for item in HERBS},
        "source_ids": {item["name"]: str(item["id"]) for item in SOURCES},
        "user_ids": {item["username"]: str(item["id"]) for item in USERS},
    }


@pytest_asyncio.fixture(autouse=True)
async def seeded_demo_environment() -> AsyncIterator[None]:
    await engine.dispose()
    await seed_postgres()
    await seed_neo4j()
    yield
    await graph_service.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(seeded_demo_environment):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture(scope="session")
def db_session_factory():
    return AsyncSessionLocal


@pytest_asyncio.fixture
async def neo4j_driver(seeded_demo_environment):
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        yield driver
    finally:
        await driver.close()


@pytest_asyncio.fixture
async def load_graph_node(neo4j_driver):
    async def _load_graph_node(node_id: str) -> dict | None:
        query = """
        MATCH (n)
        WHERE n.id = $node_id
        RETURN n
        """
        async with neo4j_driver.session() as session:
            result = await session.run(query, node_id=node_id)
            record = await result.single()
            return dict(record["n"]) if record else None

    return _load_graph_node
