from neomodel import (
    AsyncRelationshipFrom,
    AsyncRelationshipTo,
    AsyncStructuredNode,
    AsyncStructuredRel,
    DateTimeProperty,
    FloatProperty,
    IntegerProperty,
    StringProperty,
)


class BaseRel(AsyncStructuredRel):
    status = StringProperty(default="待验证", db_property="状态")
    verification_id = StringProperty(db_property="验证标识")
    verified_by = StringProperty(db_property="验证人")
    verified_at = DateTimeProperty(db_property="验证时间")


class ContainsRel(BaseRel):
    quantity = StringProperty(db_property="用量")


class ProcessedByRel(BaseRel):
    duration = StringProperty(db_property="时长")
    conditions = StringProperty(db_property="条件")
    start_date = StringProperty(db_property="开始日期")
    end_date = StringProperty(db_property="结束日期")


class HasTraitRel(BaseRel):
    value = StringProperty(required=True, db_property="取值")
    observation = StringProperty(db_property="观察")
    year_range = StringProperty(db_property="年份范围")


class StoredForRel(BaseRel):
    years = IntegerProperty(db_property="年份")
    start_date = StringProperty(db_property="开始日期")
    end_date = StringProperty(db_property="结束日期")


class DerivedFromRel(BaseRel):
    source_id = StringProperty(db_property="导入源")
    evidence_id = StringProperty(db_property="证据标识")


class SimilarToRel(BaseRel):
    similarity_score = FloatProperty(default=0.0)


class GraphNodeBase(AsyncStructuredNode):
    identifier = StringProperty(required=True, unique_index=True, db_property="标识")
    name = StringProperty(required=True, unique_index=True, db_property="名称")
    source = StringProperty(db_property="来源")
    imported_at = DateTimeProperty(db_property="导入时间")
    status = StringProperty(default="待验证", db_property="状态")
    verification_id = StringProperty(db_property="验证标识")
    verified_by = StringProperty(db_property="验证人")
    verified_at = DateTimeProperty(db_property="验证时间")


class ComponentNode(GraphNodeBase):
    __label__ = "成分"

    chemical_formula = StringProperty(db_property="化学式")
    extracted_from = AsyncRelationshipFrom("HerbNode", "包含成分", model=ContainsRel)


class VariantNode(GraphNodeBase):
    __label__ = "品种"

    parent_herb = StringProperty(db_property="所属药材")
    description = StringProperty(db_property="说明")
    variant_of = AsyncRelationshipTo("HerbNode", "属于药材", model=BaseRel)


class ProcessNode(GraphNodeBase):
    __label__ = "工艺"

    description = StringProperty(db_property="说明")
    min_duration = StringProperty(db_property="最短时长")
    conditions = StringProperty(db_property="条件")


class TraitNode(GraphNodeBase):
    __label__ = "性状"

    trait_category = StringProperty(db_property="分类")
    description = StringProperty(db_property="说明")
    observation_method = StringProperty(db_property="观察方法")


class TimePointNode(GraphNodeBase):
    __label__ = "时间点"

    years = IntegerProperty(unique_index=True, db_property="年份")
    description = StringProperty(db_property="说明")
    quality_indicator = StringProperty(db_property="质量指标")


class EfficacyNode(GraphNodeBase):
    __label__ = "功效"

    category = StringProperty(db_property="分类")


class FlavorNode(GraphNodeBase):
    __label__ = "性味"

    nature = StringProperty(db_property="药性")


class MeridianNode(GraphNodeBase):
    __label__ = "归经"


class DiseaseNode(GraphNodeBase):
    __label__ = "病证"

    tcm_type = StringProperty(db_property="中医类型")


class SourceNode(GraphNodeBase):
    __label__ = "来源"


class EvidenceNode(GraphNodeBase):
    __label__ = "证据"

    content = StringProperty(required=True, db_property="原文")
    source_name = StringProperty(db_property="来源")
    page_reference = StringProperty(db_property="页码")
    derived_from = AsyncRelationshipTo("SourceNode", "派生自", model=DerivedFromRel)


class HerbNode(GraphNodeBase):
    __label__ = "药材"

    category = StringProperty(db_property="分类")
    herb_type = StringProperty(db_property="类型")
    contains = AsyncRelationshipTo("ComponentNode", "包含成分", model=ContainsRel)
    parent_of = AsyncRelationshipTo("HerbNode", "父类", model=BaseRel)
    child_of = AsyncRelationshipTo("HerbNode", "子类", model=BaseRel)
    originated_from = AsyncRelationshipTo("SourceNode", "来源于", model=BaseRel)
    has_variant = AsyncRelationshipTo("VariantNode", "具有品种", model=BaseRel)
    processed_by = AsyncRelationshipTo("ProcessNode", "经过工艺", model=ProcessedByRel)
    has_trait = AsyncRelationshipTo("TraitNode", "具有性状", model=HasTraitRel)
    stored_for = AsyncRelationshipTo("TimePointNode", "储存时间", model=StoredForRel)
    has_efficacy = AsyncRelationshipTo("EfficacyNode", "具有功效", model=BaseRel)
    has_flavor = AsyncRelationshipTo("FlavorNode", "具有性味", model=BaseRel)
    enters_meridian = AsyncRelationshipTo("MeridianNode", "归于经脉", model=BaseRel)
    treats = AsyncRelationshipTo("DiseaseNode", "治疗病证", model=BaseRel)
    similar_to = AsyncRelationshipTo("HerbNode", "相似于", model=SimilarToRel)


class FormulaNode(GraphNodeBase):
    __label__ = "方剂"

    composition_text = StringProperty(db_property="组成原文")
    source_book = StringProperty(db_property="出处书名")


class MedicalCaseNode(GraphNodeBase):
    __label__ = "医案"


class AcupointNode(GraphNodeBase):
    __label__ = "穴位"


class TreatmentMethodNode(GraphNodeBase):
    __label__ = "治法"


class PreparedHerbNode(GraphNodeBase):
    __label__ = "饮片"

    prepared_from_herb = StringProperty(db_property="来自药材")
    processing_method_text = StringProperty(db_property="炮制方法")


NODE_MODEL_MAP = {
    "药材": HerbNode,
    "饮片": PreparedHerbNode,
    "成分": ComponentNode,
    "品种": VariantNode,
    "工艺": ProcessNode,
    "性状": TraitNode,
    "时间点": TimePointNode,
    "功效": EfficacyNode,
    "性味": FlavorNode,
    "归经": MeridianNode,
    "病证": DiseaseNode,
    "来源": SourceNode,
    "证据": EvidenceNode,
    "方剂": FormulaNode,
    "医案": MedicalCaseNode,
    "穴位": AcupointNode,
    "治法": TreatmentMethodNode,
    "Herb": HerbNode,
    "PreparedHerb": PreparedHerbNode,
    "Component": ComponentNode,
    "Variant": VariantNode,
    "Process": ProcessNode,
    "Trait": TraitNode,
    "TimePoint": TimePointNode,
    "Efficacy": EfficacyNode,
    "Flavor": FlavorNode,
    "Meridian": MeridianNode,
    "Disease": DiseaseNode,
    "Source": SourceNode,
    "Evidence": EvidenceNode,
    "Formula": FormulaNode,
    "MedicalCase": MedicalCaseNode,
    "Acupoint": AcupointNode,
    "TreatmentMethod": TreatmentMethodNode,
}


REL_TYPE_TO_ATTR = {
    "包含成分": "contains",
    "父类": "parent_of",
    "子类": "child_of",
    "来源于": "originated_from",
    "属于药材": "variant_of",
    "具有品种": "has_variant",
    "经过工艺": "processed_by",
    "具有性状": "has_trait",
    "储存时间": "stored_for",
    "具有功效": "has_efficacy",
    "具有性味": "has_flavor",
    "归于经脉": "enters_meridian",
    "治疗病证": "treats",
    "相似于": "similar_to",
    "派生自": "derived_from",
}
