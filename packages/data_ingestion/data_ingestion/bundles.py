from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from knowledge_model.constants import EdgeType


class BundleEdge(BaseModel):
    source: str = Field(description="源节点标识")
    target: str = Field(description="目标节点标识")
    type: EdgeType = Field(description="边类型")
    properties: dict[str, Any] = Field(default_factory=dict, description="边属性")

    model_config = ConfigDict(use_enum_values=False)


class UnifiedGraphBundle(BaseModel):
    nodes: list[Any] = Field(default_factory=list, description="统一节点集合")
    edges: list[BundleEdge] = Field(default_factory=list, description="统一边集合")
    records: list[Any] = Field(default_factory=list, description="统一导入记录集合")
    warnings: list[str] = Field(default_factory=list, description="处理警告列表")
    errors: list[str] = Field(default_factory=list, description="处理错误列表")
    stats: dict[str, Any] = Field(default_factory=dict, description="处理统计信息")

    model_config = ConfigDict(use_enum_values=False, arbitrary_types_allowed=True)
