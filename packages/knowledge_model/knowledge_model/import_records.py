from pydantic import BaseModel, ConfigDict, Field

from .constants import EdgeType, NodeStatus, NodeType


class GraphImportEdge(BaseModel):
    type: EdgeType
    target: str
    properties: dict[str, object] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=False)


class GraphImportRecord(BaseModel):
    node_type: NodeType | None = None
    node_name: str
    source: str
    status: NodeStatus = NodeStatus.PENDING
    properties: dict[str, object] = Field(default_factory=dict)
    edges: list[GraphImportEdge] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=False)
