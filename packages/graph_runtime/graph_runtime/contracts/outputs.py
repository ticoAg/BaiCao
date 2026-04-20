from pydantic import BaseModel, ConfigDict, Field


class GraphSubgraphMeta(BaseModel):
    center_node_id: str | None = Field(default=None, description="中心节点 ID")
    actual_depth: int = Field(default=0, description="实际探索深度")
    fallback_used: bool = Field(default=False, description="是否使用只读 Cypher fallback")
    node_count: int = Field(default=0, description="返回节点数量")
    edge_count: int = Field(default=0, description="返回边数量")

    model_config = ConfigDict(use_enum_values=False)


class GraphAgentAnswer(BaseModel):
    answer: str = Field(description="自然语言回答")
    evidence: list[dict] = Field(default_factory=list, description="证据摘要列表")
    related_nodes: list[dict] = Field(default_factory=list, description="相关节点")
    related_edges: list[dict] = Field(default_factory=list, description="相关边")
    subgraph_meta: GraphSubgraphMeta = Field(description="子图元信息")
    reasoning_trace: list[dict] = Field(default_factory=list, description="推理轨迹摘要")
    tool_calls: list[dict] = Field(default_factory=list, description="工具调用记录")

    model_config = ConfigDict(use_enum_values=False)
