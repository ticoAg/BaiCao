from collections.abc import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from ...graph_runtime_backend import ApiGraphRuntimeBackend
from ..knowledge_mcp.handlers import KnowledgeMcpHandlers


class ReadCypherArgs(BaseModel):
    query: str = Field(description="只读 Cypher 查询")


def build_read_cypher_tool(
    backend_factory: Callable[[], ApiGraphRuntimeBackend] | None = None,
) -> StructuredTool:
    handlers = KnowledgeMcpHandlers(backend_factory=backend_factory)

    async def _read_cypher(query: str):
        return await handlers.read_cypher({"query": query})

    return StructuredTool.from_function(
        coroutine=_read_cypher,
        name="read_cypher",
        description="只读 Cypher。属性键用 名称/标识，不要写 n.id / n.name。仅在基础图工具不够时使用。",
        args_schema=ReadCypherArgs,
    )
