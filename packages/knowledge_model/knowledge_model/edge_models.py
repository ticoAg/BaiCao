from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .constants import EdgeType, NodeStatus


class BaseEdgeModel(BaseModel):
    type: EdgeType = Field(description="边类型")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="边审核状态")
    verification_id: str | None = Field(default=None, description="审核记录标识")
    verified_by: str | None = Field(default=None, description="审核人")
    verified_at: datetime | None = Field(default=None, description="审核完成时间")

    model_config = ConfigDict(use_enum_values=False)


class ContainsEdgeModel(BaseEdgeModel):
    type: EdgeType = Field(default=EdgeType.CONTAINS, description="边类型：包含")
    quantity: str | None = Field(default=None, description="包含数量或比例说明")
