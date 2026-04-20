from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend


class ReadCypherArgs(BaseModel):
    query: str = Field(description="只读 Cypher 查询")


def build_read_cypher_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    def _backend() -> ApiGraphRuntimeBackend:
        return backend_factory() if backend_factory else ApiGraphRuntimeBackend()

    async def _read_cypher(query: str):
        return await _backend().execute_readonly_cypher(query)

    return StructuredTool.from_function(
        coroutine=_read_cypher,
        name="read_cypher",
        description="执行只读 Cypher 查询。仅在基础图工具无法收敛时作为低层 escape hatch 使用。",
        args_schema=ReadCypherArgs,
    )
