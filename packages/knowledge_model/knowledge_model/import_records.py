from pydantic import BaseModel, ConfigDict, Field

from .constants import EdgeType, NodeStatus, NodeType


class GraphImportEdge(BaseModel):
    type: EdgeType = Field(description="导入边类型")
    target: str = Field(description="目标节点名称或标识")
    properties: dict[str, object] = Field(default_factory=dict, description="边属性集合")

    model_config = ConfigDict(use_enum_values=False)


class GraphImportRecord(BaseModel):
    node_type: NodeType | None = Field(default=None, description="导入节点类型")
    node_name: str = Field(description="导入节点名称")
    source: str = Field(description="导入数据来源")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="导入节点审核状态")
    properties: dict[str, object] = Field(default_factory=dict, description="节点属性集合")
    edges: list[GraphImportEdge] = Field(default_factory=list, description="与当前节点关联的边列表")

    model_config = ConfigDict(use_enum_values=False)
