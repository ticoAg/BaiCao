from enum import StrEnum
from typing import Literal


class NodeType(StrEnum):
    HERB = "药材"
    COMPONENT = "成分"
    VARIANT = "品种"
    PROCESS = "工艺"
    TRAIT = "性状"
    EFFICACY = "功效"
    FLAVOR = "性味"
    MERIDIAN = "归经"
    DISEASE = "病证"
    TIMEPOINT = "时间点"
    SOURCE = "来源"


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


NODE_TYPE_TO_NEO4J_LABEL: dict[NodeType, str] = {
    NodeType.HERB: "Herb",
    NodeType.COMPONENT: "Component",
    NodeType.VARIANT: "Variant",
    NodeType.PROCESS: "Process",
    NodeType.TRAIT: "Trait",
    NodeType.EFFICACY: "Efficacy",
    NodeType.FLAVOR: "Flavor",
    NodeType.MERIDIAN: "Meridian",
    NodeType.DISEASE: "Disease",
    NodeType.TIMEPOINT: "TimePoint",
    NodeType.SOURCE: "Source",
}

NEO4J_LABEL_TO_NODE_TYPE: dict[str, NodeType] = {
    neo4j_label: node_type for node_type, neo4j_label in NODE_TYPE_TO_NEO4J_LABEL.items()
}

NODE_TYPE_ALIASES: dict[str, NodeType] = {
    **{node_type.value: node_type for node_type in NodeType},
    **NEO4J_LABEL_TO_NODE_TYPE,
}


def parse_node_type(value: NodeType | str) -> NodeType:
    if isinstance(value, NodeType):
        return value

    normalized = str(value).strip()
    if normalized in NODE_TYPE_ALIASES:
        return NODE_TYPE_ALIASES[normalized]
    return NodeType(normalized)


def to_neo4j_label(value: NodeType | str) -> str:
    return NODE_TYPE_TO_NEO4J_LABEL[parse_node_type(value)]


NodeTypeLiteral = Literal[
    "药材",
    "成分",
    "品种",
    "工艺",
    "性状",
    "功效",
    "性味",
    "归经",
    "病证",
    "时间点",
    "来源",
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
