from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend


class SearchNodesArgs(BaseModel):
    query: str = Field(description="节点模糊查询关键词，优先用于定位锚点")
    label: str | None = Field(default=None, description="可选节点类型过滤")
    limit: int = Field(default=5, ge=1, le=20, description="候选节点上限")


def build_search_nodes_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    def _backend() -> ApiGraphRuntimeBackend:
        return backend_factory() if backend_factory else ApiGraphRuntimeBackend()

    async def _search_nodes(query: str, label: str | None = None, limit: int = 5):
        return await _backend().search_nodes(query=query, label=label, limit=limit)

    return StructuredTool.from_function(
        coroutine=_search_nodes,
        name="search_nodes",
        description=(
            "按自然语言关键词模糊查询图谱节点。优先用于定位锚点，"
            "当问题没有直接给出明确实体时先使用该工具收敛候选节点。"
        ),
        args_schema=SearchNodesArgs,
    )
