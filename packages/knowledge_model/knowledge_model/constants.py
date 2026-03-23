from enum import StrEnum
from typing import Literal


class NodeType(StrEnum):
    HERB = "Herb"
    COMPONENT = "Component"
    VARIANT = "Variant"
    PROCESS = "Process"
    TRAIT = "Trait"
    EFFICACY = "Efficacy"
    FLAVOR = "Flavor"
    MERIDIAN = "Meridian"
    DISEASE = "Disease"
    TIMEPOINT = "TimePoint"
    SOURCE = "Source"


class EdgeType(StrEnum):
    CONTAINS = "CONTAINS"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    HAS_VARIANT = "HAS_VARIANT"
    VARIANT_OF = "VARIANT_OF"
    PROCESSED_BY = "PROCESSED_BY"
    APPLIES_TO = "APPLIES_TO"
    STORED_FOR = "STORED_FOR"
    HAS_TRAIT = "HAS_TRAIT"
    OBSERVED_IN = "OBSERVED_IN"
    HAS_EFFICACY = "HAS_EFFICACY"
    HAS_FLAVOR = "HAS_FLAVOR"
    ENTERS_MERIDIAN = "ENTERS_MERIDIAN"
    TREATS = "TREATS"
    INTERACTS_WITH = "INTERACTS_WITH"
    SIMILAR_TO = "SIMILAR_TO"
    ORIGINATED_FROM = "ORIGINATED_FROM"


class NodeStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class HerbType(StrEnum):
    BASE = "base"
    BYPRODUCT = "byproduct"


class TraitCategory(StrEnum):
    EXTERNAL = "external"
    INTERNAL = "internal"
    CHEMICAL = "chemical"


NodeTypeLiteral = Literal[
    "Herb",
    "Component",
    "Variant",
    "Process",
    "Trait",
    "Efficacy",
    "Flavor",
    "Meridian",
    "Disease",
    "TimePoint",
    "Source",
]

EdgeTypeLiteral = Literal[
    "CONTAINS",
    "EXTRACTED_FROM",
    "HAS_VARIANT",
    "VARIANT_OF",
    "PROCESSED_BY",
    "APPLIES_TO",
    "STORED_FOR",
    "HAS_TRAIT",
    "OBSERVED_IN",
    "HAS_EFFICACY",
    "HAS_FLAVOR",
    "ENTERS_MERIDIAN",
    "TREATS",
    "INTERACTS_WITH",
    "SIMILAR_TO",
    "ORIGINATED_FROM",
]
