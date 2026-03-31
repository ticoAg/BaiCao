from .constants import EdgeType, NodeType


NODE_TYPE_LABELS: dict[NodeType, str] = {
    NodeType.HERB: "药材",
    NodeType.PREPARED_HERB: "饮片",
    NodeType.COMPONENT: "成分",
    NodeType.VARIANT: "品种",
    NodeType.PROCESS: "工艺",
    NodeType.TRAIT: "性状",
    NodeType.EFFICACY: "功效",
    NodeType.FLAVOR: "性味",
    NodeType.MERIDIAN: "归经",
    NodeType.DISEASE: "病证",
    NodeType.TIMEPOINT: "时间点",
    NodeType.SOURCE: "来源",
    NodeType.EVIDENCE: "证据",
}

EDGE_TYPE_LABELS: dict[EdgeType, str] = {
    EdgeType.HAS_PREPARED_FORM: "具有饮片",
    EdgeType.CONTAINS: EdgeType.CONTAINS.value,
    EdgeType.EXTRACTED_FROM: EdgeType.EXTRACTED_FROM.value,
    EdgeType.HAS_VARIANT: EdgeType.HAS_VARIANT.value,
    EdgeType.VARIANT_OF: EdgeType.VARIANT_OF.value,
    EdgeType.PROCESSED_BY: EdgeType.PROCESSED_BY.value,
    EdgeType.APPLIES_TO: EdgeType.APPLIES_TO.value,
    EdgeType.STORED_FOR: EdgeType.STORED_FOR.value,
    EdgeType.HAS_TRAIT: EdgeType.HAS_TRAIT.value,
    EdgeType.OBSERVED_IN: EdgeType.OBSERVED_IN.value,
    EdgeType.HAS_EFFICACY: EdgeType.HAS_EFFICACY.value,
    EdgeType.HAS_FLAVOR: EdgeType.HAS_FLAVOR.value,
    EdgeType.ENTERS_MERIDIAN: EdgeType.ENTERS_MERIDIAN.value,
    EdgeType.TREATS: EdgeType.TREATS.value,
    EdgeType.INTERACTS_WITH: EdgeType.INTERACTS_WITH.value,
    EdgeType.SIMILAR_TO: EdgeType.SIMILAR_TO.value,
    EdgeType.PARENT_OF: EdgeType.PARENT_OF.value,
    EdgeType.CHILD_OF: EdgeType.CHILD_OF.value,
    EdgeType.ORIGINATED_FROM: EdgeType.ORIGINATED_FROM.value,
    EdgeType.DERIVED_FROM: EdgeType.DERIVED_FROM.value,
    EdgeType.SUPPORTED_BY: "由证据支持",
}
