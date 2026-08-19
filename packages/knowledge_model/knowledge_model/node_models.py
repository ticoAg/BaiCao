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


class PreparedHerbNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.PREPARED_HERB, description="节点类型：饮片")
    prepared_from_herb: str | None = Field(default=None, description="对应药材名称")
    processing_method_text: str | None = Field(default=None, description="炮制方法原文")
    description: str | None = Field(default=None, description="饮片说明")


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


class SymptomNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.SYMPTOM, description="节点类型：症状")
    category: str | None = Field(default=None, description="症状分类")
    description: str | None = Field(default=None, description="症状说明")


class FormulaNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.FORMULA, description="节点类型：方剂")
    composition_text: str | None = Field(default=None, description="组成原文")
    source_book: str | None = Field(default=None, description="出处书名")


class MedicalCaseNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.MEDICAL_CASE, description="节点类型：医案")
    chief_complaint: str | None = Field(default=None, description="主诉")
    unit_id: str | None = Field(default=None, description="来源单元，如章节")


class AcupointNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.ACUPOINT, description="节点类型：穴位")
    meridian: str | None = Field(default=None, description="所属经脉")


class TreatmentMethodNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.TREATMENT_METHOD, description="节点类型：治法")
    category: str | None = Field(default=None, description="针刺/推拿/祝由/导引等")


class TimePointNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.TIMEPOINT, description="节点类型：时间点")
    years: int | None = Field(default=None, description="对应年份数值")
    quality_indicator: str | None = Field(default=None, description="质量指标说明")


class EvidenceNodeModel(BaseNodeModel):
    type: NodeType = Field(default=NodeType.EVIDENCE, description="节点类型：证据")
    raw_text: str = Field(description="证据原文")
    source_provider: str = Field(description="来源提供方")
    dataset_name: str = Field(description="来源数据集名称")
    file_path: str = Field(description="来源文件路径")
    entry_title: str = Field(description="条目标题")
    line_start: int = Field(description="起始行号")
    line_end: int = Field(description="结束行号")
    chunk_hash: str = Field(description="证据块哈希")
