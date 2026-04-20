from .entity_fuzzy_recall import recall_entity_keywords
from .schema_semantic_mapping import SCHEMA_SEMANTIC_RULES


def build_graph_plan(question: str) -> dict:
    plan = {
        "question": question,
        "entity_hints": recall_entity_keywords(question),
        "target_node_types": [],
        "target_edge_types": [],
        "search_mode": "adaptive",
    }
    for rule in SCHEMA_SEMANTIC_RULES:
        if any(keyword in question for keyword in rule["keywords"]):
            plan["target_node_types"].extend(rule["target_node_types"])
            plan["target_edge_types"].extend(rule["target_edge_types"])
    plan["target_node_types"] = list(dict.fromkeys(plan["target_node_types"]))
    plan["target_edge_types"] = list(dict.fromkeys(plan["target_edge_types"]))
    return plan
