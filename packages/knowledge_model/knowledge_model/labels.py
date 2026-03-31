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
    EdgeType.ORIGINATED_FROM: "来源于",
    EdgeType.SUPPORTED_BY: "由证据支持",
}
