from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend
from ..knowledge_mcp.handlers import KnowledgeMcpHandlers


class ExpandNeighborsArgs(BaseModel):
    node_id: str = Field(description="已定位锚点节点的标识，例如 formula-乌梅丸")
    depth: int = Field(default=1, ge=1, le=2, description="邻居展开深度")
    limit: int = Field(default=20, ge=1, le=50, description="子图节点上限")


def build_expand_neighbors_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    handlers = KnowledgeMcpHandlers(backend_factory=backend_factory)

    async def _expand_neighbors(node_id: str, depth: int = 1, limit: int = 20):
        return await handlers.expand_neighbors(
            {"node_id": node_id, "depth": depth, "limit": limit}
        )

    return StructuredTool.from_function(
        coroutine=_expand_neighbors,
        name="expand_neighbors",
        description="围绕已知锚点节点做 1-hop 或 2-hop 图游走，适合在定位锚点后继续扩展依据子图。",
        args_schema=ExpandNeighborsArgs,
    )
