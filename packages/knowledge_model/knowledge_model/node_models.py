from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .constants import HerbType, NodeStatus, NodeType


class BaseNodeModel(BaseModel):
    id: str = Field(description="节点唯一标识")
    name: str = Field(description="节点展示名称")
    type: NodeType = Field(description="节点类型")
    source: str | None = Field(default=None, description="数据来源")
    imported_at: datetime | None = Field(default=None, description="导入时间")
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="节点审核状态")
    verification_id: str | None = Field(default=None, description="审核记录标识")
    verified_by: str | None = Field(default=None, description="审核人")
    verified_at: datetime | None = Field(default=None, description="审核完成时间")

    model_config = ConfigDict(use_enum_values=False, frozen=False)


class HerbNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.HERB, description="节点类型：药材")
    herb_type: HerbType = Field(default=HerbType.BASE, description="药材细分类型")
    category: str | None = Field(default=None, description="药材分类")
    description: str | None = Field(default=None, description="药材说明")


class ComponentNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.COMPONENT, description="节点类型：成分")
    chemical_formula: str | None = Field(default=None, description="化学式")


class VariantNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.VARIANT, description="节点类型：品种")
    parent_herb: str | None = Field(default=None, description="所属药材名称或标识")
    description: str | None = Field(default=None, description="品种说明")


class EfficacyNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.EFFICACY, description="节点类型：功效")
    category: str | None = Field(default=None, description="功效分类")


class FlavorNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.FLAVOR, description="节点类型：性味")
    nature: str | None = Field(default=None, description="性味属性")


class MeridianNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.MERIDIAN, description="节点类型：归经")


class DiseaseNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.DISEASE, description="节点类型：病证")
    tcm_type: str | None = Field(default=None, description="中医病证分类")


class TimePointNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.TIMEPOINT, description="节点类型：时间点")
    years: int | None = Field(default=None, description="对应年份数值")
    quality_indicator: str | None = Field(default=None, description="质量指标说明")
