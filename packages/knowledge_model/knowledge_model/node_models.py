from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .constants import HerbType, NodeStatus, NodeType


class BaseNodeModel(BaseModel):
    id: str
    name: str
    type: NodeType
    source: str | None = None
    imported_at: datetime | None = None
    status: NodeStatus = NodeStatus.PENDING
    verification_id: str | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None

    model_config = ConfigDict(use_enum_values=False, frozen=False)


class HerbNodeModel(BaseNodeModel):
    type: NodeType = NodeType.HERB
    herb_type: HerbType = HerbType.BASE
    category: str | None = None
    description: str | None = None


class ComponentNodeModel(BaseNodeModel):
    type: NodeType = NodeType.COMPONENT
    chemical_formula: str | None = None


class VariantNodeModel(BaseNodeModel):
    type: NodeType = NodeType.VARIANT
    parent_herb: str | None = None
    description: str | None = None


class EfficacyNodeModel(BaseNodeModel):
    type: NodeType = NodeType.EFFICACY
    category: str | None = None


class FlavorNodeModel(BaseNodeModel):
    type: NodeType = NodeType.FLAVOR
    nature: str | None = None


class MeridianNodeModel(BaseNodeModel):
    type: NodeType = NodeType.MERIDIAN


class DiseaseNodeModel(BaseNodeModel):
    type: NodeType = NodeType.DISEASE
    tcm_type: str | None = None


class TimePointNodeModel(BaseNodeModel):
    type: NodeType = NodeType.TIMEPOINT
    years: int | None = None
    quality_indicator: str | None = None
