import asyncio

import pytest

from graph_runtime.service.graph_facade import GraphFacade


class FakeBackend:
    async def search_nodes(self, query: str, label: str | None = None, limit: int = 20):
        return [{"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]}]

    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        return {
            "center": {"id": node_id, "name": "黄芩", "labels": ["药材"]},
            "nodes": [{"id": node_id, "name": "黄芩", "labels": ["药材"]}],
            "edges": [],
        }

    async def execute_readonly_cypher(self, query: str):
        return [{"name": "黄芩"}]


async def _run_graph_facade_delegates_search_and_expand():
    facade = GraphFacade(FakeBackend())

    matches = await facade.search_nodes("黄芩")
    subgraph = await facade.expand_neighbors("药材:黄芩", depth=1)

    assert matches[0]["name"] == "黄芩"
    assert subgraph["center"]["id"] == "药材:黄芩"


def test_graph_facade_delegates_search_and_expand():
    asyncio.run(_run_graph_facade_delegates_search_and_expand())


async def _run_graph_facade_exposes_readonly_cypher():
    facade = GraphFacade(FakeBackend())

    rows = await facade.read_cypher("MATCH (n) RETURN n.name AS name LIMIT 1")

    assert rows == [{"name": "黄芩"}]


def test_graph_facade_exposes_readonly_cypher():
    asyncio.run(_run_graph_facade_exposes_readonly_cypher())


async def _run_graph_facade_blocks_write_cypher():
    facade = GraphFacade(FakeBackend())

    with pytest.raises(ValueError, match="只允许执行只读 Cypher"):
        await facade.read_cypher("MATCH (n) SET n.name = 'foo' RETURN n")


def test_graph_facade_blocks_write_cypher():
    asyncio.run(_run_graph_facade_blocks_write_cypher())
