import asyncio

from graph_runtime.primitives.bfs import bfs_walk
from graph_runtime.primitives.dfs import dfs_walk


class WalkBackend:
    async def expand_neighbors(self, node_id: str, depth: int = 1, limit: int = 20):
        graph = {
            "药材:黄芩": {
                "center": {"id": "药材:黄芩", "name": "黄芩"},
                "nodes": [
                    {"id": "功效:清热燥湿", "name": "清热燥湿"},
                    {"id": "归经:肺经", "name": "肺经"},
                ],
                "edges": [
                    {
                        "source": {"id": "药材:黄芩"},
                        "target": {"id": "功效:清热燥湿"},
                        "type": "具有功效",
                    },
                    {
                        "source": {"id": "药材:黄芩"},
                        "target": {"id": "归经:肺经"},
                        "type": "归于经脉",
                    },
                ],
            }
        }
        return graph[node_id]


async def _run_bfs_walk_respects_node_budget():
    result = await bfs_walk(WalkBackend(), seed_node_id="药材:黄芩", max_depth=2, node_budget=2)
    assert len(result["nodes"]) <= 2


def test_bfs_walk_respects_node_budget():
    asyncio.run(_run_bfs_walk_respects_node_budget())


async def _run_dfs_walk_returns_trace():
    result = await dfs_walk(WalkBackend(), seed_node_id="药材:黄芩", max_depth=2, node_budget=4)
    assert result["trace"][0]["strategy"] == "dfs"


def test_dfs_walk_returns_trace():
    asyncio.run(_run_dfs_walk_returns_trace())
