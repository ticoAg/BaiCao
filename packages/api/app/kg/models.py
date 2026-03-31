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
    status = StringProperty(default="pending")
    verification_id = StringProperty()
    verified_by = StringProperty()
    verified_at = DateTimeProperty()


class ContainsRel(BaseRel):
    quantity = StringProperty()


class ProcessedByRel(BaseRel):
    duration = StringProperty()
    conditions = StringProperty()
    start_date = StringProperty()
    end_date = StringProperty()


class HasTraitRel(BaseRel):
    value = StringProperty(required=True)
    observation = StringProperty()
    year_range = StringProperty()


class StoredForRel(BaseRel):
    years = IntegerProperty()
    start_date = StringProperty()
    end_date = StringProperty()


class DerivedFromRel(BaseRel):
    source_id = StringProperty()
    evidence_id = StringProperty()


class SimilarToRel(BaseRel):
    similarity_score = FloatProperty(default=0.0)


class GraphNodeBase(AsyncStructuredNode):
    identifier = StringProperty(required=True, unique_index=True, db_property="id")
    name = StringProperty(required=True, unique_index=True)
    source = StringProperty()
    imported_at = DateTimeProperty()
    status = StringProperty(default="pending")
    verification_id = StringProperty()
    verified_by = StringProperty()
    verified_at = DateTimeProperty()


class ComponentNode(GraphNodeBase):
    __label__ = "Component"

    chemical_formula = StringProperty()
    extracted_from = AsyncRelationshipFrom("HerbNode", "包含成分", model=ContainsRel)


class VariantNode(GraphNodeBase):
    __label__ = "Variant"

    parent_herb = StringProperty()
    description = StringProperty()
    variant_of = AsyncRelationshipTo("HerbNode", "属于药材", model=BaseRel)


class ProcessNode(GraphNodeBase):
    __label__ = "Process"

    description = StringProperty()
    min_duration = StringProperty()
    conditions = StringProperty()


class TraitNode(GraphNodeBase):
    __label__ = "Trait"

    trait_category = StringProperty(db_property="category")
    description = StringProperty()
    observation_method = StringProperty()


class TimePointNode(GraphNodeBase):
    __label__ = "TimePoint"

    years = IntegerProperty(unique_index=True)
    description = StringProperty()
    quality_indicator = StringProperty()


class EfficacyNode(GraphNodeBase):
    __label__ = "Efficacy"

    category = StringProperty()


class FlavorNode(GraphNodeBase):
    __label__ = "Flavor"

    nature = StringProperty()


class MeridianNode(GraphNodeBase):
    __label__ = "Meridian"


class DiseaseNode(GraphNodeBase):
    __label__ = "Disease"

    tcm_type = StringProperty()


class SourceNode(GraphNodeBase):
    __label__ = "Source"


class EvidenceNode(GraphNodeBase):
    __label__ = "Evidence"

    content = StringProperty(required=True)
    source_name = StringProperty()
    page_reference = StringProperty()
    derived_from = AsyncRelationshipTo("SourceNode", "派生自", model=DerivedFromRel)


class HerbNode(GraphNodeBase):
    __label__ = "Herb"

    category = StringProperty()
    herb_type = StringProperty(db_property="type")
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


NODE_MODEL_MAP = {
    "Herb": HerbNode,
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
