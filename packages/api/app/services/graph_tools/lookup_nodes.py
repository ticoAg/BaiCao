from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend
from ..knowledge_mcp.handlers import KnowledgeMcpHandlers


class LookupNodesArgs(BaseModel):
    node_ids: list[str] = Field(description="需要精确读取的节点 id 列表")


def build_lookup_nodes_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    handlers = KnowledgeMcpHandlers(backend_factory=backend_factory)

    async def _lookup_nodes(node_ids: list[str]):
        return await handlers.lookup_nodes({"node_ids": node_ids})

    return StructuredTool.from_function(
        coroutine=_lookup_nodes,
        name="lookup_nodes",
        description="按节点 id 精确读取节点详情，适合在已有候选后回看节点属性而不是重复做模糊查询。",
        args_schema=LookupNodesArgs,
    )
