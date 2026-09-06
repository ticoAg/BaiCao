from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend
from ..knowledge_mcp.handlers import KnowledgeMcpHandlers


class SearchNodesArgs(BaseModel):
    query: str = Field(description="节点模糊查询关键词，优先用于定位锚点")
    label: str | None = Field(default=None, description="可选中文节点类型，如 方剂/医案/药材")
    limit: int = Field(default=10, ge=1, le=20, description="候选节点上限")


def build_search_nodes_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    handlers = KnowledgeMcpHandlers(backend_factory=backend_factory)

    async def _search_nodes(query: str, label: str | None = None, limit: int = 10):
        return await handlers.search_nodes({"query": query, "label": label, "limit": limit})

    return StructuredTool.from_function(
        coroutine=_search_nodes,
        name="search_nodes",
        description=(
            "按自然语言关键词模糊查询图谱节点。优先用于定位锚点，"
            "当问题没有直接给出明确实体时先使用该工具收敛候选节点。"
        ),
        args_schema=SearchNodesArgs,
    )
