from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend


class SearchEdgesArgs(BaseModel):
    rel_query: str = Field(description="关系类型或关系关键词的模糊查询文本")
    source_label: str | None = Field(default=None, description="可选起点节点类型过滤")
    target_label: str | None = Field(default=None, description="可选终点节点类型过滤")
    limit: int = Field(default=10, ge=1, le=20, description="返回关系上限")


def build_search_edges_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    def _backend() -> ApiGraphRuntimeBackend:
        return backend_factory() if backend_factory else ApiGraphRuntimeBackend()

    async def _search_edges(
        rel_query: str,
        source_label: str | None = None,
        target_label: str | None = None,
        limit: int = 10,
    ):
        return await _backend().search_edges(
            rel_query=rel_query,
            source_label=source_label,
            target_label=target_label,
            limit=limit,
        )

    return StructuredTool.from_function(
        coroutine=_search_edges,
        name="search_edges",
        description=(
            "按关系关键词模糊查询图中的关系通道。"
            "当你已经知道要找的关系类型，但还没确定具体锚点时使用。"
        ),
        args_schema=SearchEdgesArgs,
    )
