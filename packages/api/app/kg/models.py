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
    extracted_from = AsyncRelationshipFrom("HerbNode", "CONTAINS", model=ContainsRel)


class VariantNode(GraphNodeBase):
    __label__ = "Variant"

    parent_herb = StringProperty()
    description = StringProperty()
    variant_of = AsyncRelationshipTo("HerbNode", "VARIANT_OF", model=BaseRel)


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
    derived_from = AsyncRelationshipTo("SourceNode", "DERIVED_FROM", model=DerivedFromRel)


class HerbNode(GraphNodeBase):
    __label__ = "Herb"

    category = StringProperty()
    herb_type = StringProperty(db_property="type")
    contains = AsyncRelationshipTo("ComponentNode", "CONTAINS", model=ContainsRel)
    parent_of = AsyncRelationshipTo("HerbNode", "PARENT_OF", model=BaseRel)
    child_of = AsyncRelationshipTo("HerbNode", "CHILD_OF", model=BaseRel)
    originated_from = AsyncRelationshipTo("SourceNode", "ORIGINATED_FROM", model=BaseRel)
    has_variant = AsyncRelationshipTo("VariantNode", "HAS_VARIANT", model=BaseRel)
    processed_by = AsyncRelationshipTo("ProcessNode", "PROCESSED_BY", model=ProcessedByRel)
    has_trait = AsyncRelationshipTo("TraitNode", "HAS_TRAIT", model=HasTraitRel)
    stored_for = AsyncRelationshipTo("TimePointNode", "STORED_FOR", model=StoredForRel)
    has_efficacy = AsyncRelationshipTo("EfficacyNode", "HAS_EFFICACY", model=BaseRel)
    has_flavor = AsyncRelationshipTo("FlavorNode", "HAS_FLAVOR", model=BaseRel)
    enters_meridian = AsyncRelationshipTo("MeridianNode", "ENTERS_MERIDIAN", model=BaseRel)
    treats = AsyncRelationshipTo("DiseaseNode", "TREATS", model=BaseRel)
    similar_to = AsyncRelationshipTo("HerbNode", "SIMILAR_TO", model=SimilarToRel)


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
    "CONTAINS": "contains",
    "PARENT_OF": "parent_of",
    "CHILD_OF": "child_of",
    "ORIGINATED_FROM": "originated_from",
    "VARIANT_OF": "variant_of",
    "HAS_VARIANT": "has_variant",
    "PROCESSED_BY": "processed_by",
    "HAS_TRAIT": "has_trait",
    "STORED_FOR": "stored_for",
    "HAS_EFFICACY": "has_efficacy",
    "HAS_FLAVOR": "has_flavor",
    "ENTERS_MERIDIAN": "enters_meridian",
    "TREATS": "treats",
    "SIMILAR_TO": "similar_to",
    "DERIVED_FROM": "derived_from",
}
