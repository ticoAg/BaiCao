from enum import StrEnum
from typing import Literal


class NodeType(StrEnum):
    HERB = "药材"
    PREPARED_HERB = "饮片"
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
    EVIDENCE = "证据"


class EdgeType(StrEnum):
    HAS_PREPARED_FORM = "具有饮片"
    CONTAINS = "包含成分"
    EXTRACTED_FROM = "提取自"
    HAS_VARIANT = "具有品种"
    VARIANT_OF = "属于药材"
    PROCESSED_BY = "经过工艺"
    APPLIES_TO = "适用于"
    STORED_FOR = "储存时间"
    HAS_TRAIT = "具有性状"
    OBSERVED_IN = "观察于"
    HAS_EFFICACY = "具有功效"
    HAS_FLAVOR = "具有性味"
    ENTERS_MERIDIAN = "归于经脉"
    TREATS = "治疗病证"
    INTERACTS_WITH = "相互作用"
    SIMILAR_TO = "相似于"
    PARENT_OF = "父类"
    CHILD_OF = "子类"
    ORIGINATED_FROM = "来源于"
    DERIVED_FROM = "派生自"
    SUPPORTED_BY = "由证据支持"


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
    NodeType.PREPARED_HERB: "PreparedHerb",
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
    NodeType.EVIDENCE: "Evidence",
}

NEO4J_LABEL_TO_NODE_TYPE: dict[str, NodeType] = {
    neo4j_label: node_type for node_type, neo4j_label in NODE_TYPE_TO_NEO4J_LABEL.items()
}

NODE_TYPE_ALIASES: dict[str, NodeType] = {
    **{node_type.value: node_type for node_type in NodeType},
    **NEO4J_LABEL_TO_NODE_TYPE,
}

EDGE_TYPE_TO_NEO4J_REL: dict[EdgeType, str] = {
    EdgeType.HAS_PREPARED_FORM: "具有饮片",
    EdgeType.CONTAINS: "包含成分",
    EdgeType.EXTRACTED_FROM: "提取自",
    EdgeType.HAS_VARIANT: "具有品种",
    EdgeType.VARIANT_OF: "属于药材",
    EdgeType.PROCESSED_BY: "经过工艺",
    EdgeType.APPLIES_TO: "适用于",
    EdgeType.STORED_FOR: "储存时间",
    EdgeType.HAS_TRAIT: "具有性状",
    EdgeType.OBSERVED_IN: "观察于",
    EdgeType.HAS_EFFICACY: "具有功效",
    EdgeType.HAS_FLAVOR: "具有性味",
    EdgeType.ENTERS_MERIDIAN: "归于经脉",
    EdgeType.TREATS: "治疗病证",
    EdgeType.INTERACTS_WITH: "相互作用",
    EdgeType.SIMILAR_TO: "相似于",
    EdgeType.PARENT_OF: "父类",
    EdgeType.CHILD_OF: "子类",
    EdgeType.ORIGINATED_FROM: "来源于",
    EdgeType.DERIVED_FROM: "派生自",
    EdgeType.SUPPORTED_BY: "由证据支持",
}

NEO4J_REL_TO_EDGE_TYPE: dict[str, EdgeType] = {
    neo4j_rel: edge_type for edge_type, neo4j_rel in EDGE_TYPE_TO_NEO4J_REL.items()
}

EDGE_TYPE_ALIASES: dict[str, EdgeType] = {
    **{edge_type.value: edge_type for edge_type in EdgeType},
    **NEO4J_REL_TO_EDGE_TYPE,
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


def parse_edge_type(value: EdgeType | str) -> EdgeType:
    if isinstance(value, EdgeType):
        return value

    normalized = str(value).strip()
    if normalized in EDGE_TYPE_ALIASES:
        return EDGE_TYPE_ALIASES[normalized]
    return EdgeType(normalized)


def to_neo4j_rel(value: EdgeType | str) -> str:
    return EDGE_TYPE_TO_NEO4J_REL[parse_edge_type(value)]


NodeTypeLiteral = Literal[
    "药材",
    "饮片",
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
    "证据",
]

EdgeTypeLiteral = Literal[
    "具有饮片",
    "包含成分",
    "提取自",
    "具有品种",
    "属于药材",
    "经过工艺",
    "适用于",
    "储存时间",
    "具有性状",
    "观察于",
    "具有功效",
    "具有性味",
    "归于经脉",
    "治疗病证",
    "相互作用",
    "相似于",
    "父类",
    "子类",
    "来源于",
    "派生自",
    "由证据支持",
]
