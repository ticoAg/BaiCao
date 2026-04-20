from pydantic import BaseModel, ConfigDict, Field


class GraphAskRequest(BaseModel):
    question: str = Field(description="用户自然语言问题")
    max_depth: int = Field(default=2, ge=1, le=5, description="默认探索深度预算")
    node_budget: int = Field(default=30, ge=1, le=500, description="节点预算")
    edge_budget: int = Field(default=60, ge=1, le=1000, description="边预算")
    tool_call_budget: int = Field(default=8, ge=1, le=30, description="工具调用预算")
    allow_read_cypher: bool = Field(default=True, description="是否允许只读 Cypher fallback")

    model_config = ConfigDict(use_enum_values=False)


class GraphExploreRequest(BaseModel):
    query: str = Field(description="探索起点查询")
    mode: str = Field(default="adaptive", description="探索模式：adaptive / bfs / dfs")
    max_depth: int = Field(default=2, ge=1, le=5)
    node_budget: int = Field(default=30, ge=1, le=500)

    model_config = ConfigDict(use_enum_values=False)
