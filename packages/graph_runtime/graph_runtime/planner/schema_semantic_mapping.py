SCHEMA_SEMANTIC_RULES = [
    {
        "keywords": ["功效", "主治", "作用"],
        "target_node_types": ["功效", "病证"],
        "target_edge_types": ["具有功效", "治疗病证"],
    },
    {
        "keywords": ["归经", "归什么经", "走什么经"],
        "target_node_types": ["归经"],
        "target_edge_types": ["归于经脉"],
    },
    {
        "keywords": ["饮片", "炮制", "切片后"],
        "target_node_types": ["饮片"],
        "target_edge_types": ["具有饮片"],
    },
    {
        "keywords": ["证据", "原文", "出处"],
        "target_node_types": ["证据"],
        "target_edge_types": ["由证据支持"],
    },
]
