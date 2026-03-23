from datetime import datetime

from pydantic import BaseModel, ConfigDict

from .constants import EdgeType, NodeStatus


class BaseEdgeModel(BaseModel):
    type: EdgeType
    status: NodeStatus = NodeStatus.PENDING
    verification_id: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None

    model_config = ConfigDict(use_enum_values=False)


class ContainsEdgeModel(BaseEdgeModel):
    type: EdgeType = EdgeType.CONTAINS
    quantity: str | None = None
