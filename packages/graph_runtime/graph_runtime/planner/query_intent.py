from dataclasses import dataclass, field
import re


ABSTRACT_QUERY_PATTERNS = [
    r"都有哪些",
    r"怎么办",
    r"怎么做",
    r"治.+都有哪些",
    r"治.+怎么做",
]


@dataclass
class QueryIntent:
    query_mode: str
    target_node_types: list[str] = field(default_factory=list)
    target_edge_types: list[str] = field(default_factory=list)
    requires_cypher_agent: bool = False


def classify_query_intent(question: str) -> QueryIntent:
    normalized = question.replace("？", "").replace("?", "").strip()
    if any(re.search(pattern, normalized) for pattern in ABSTRACT_QUERY_PATTERNS):
        return QueryIntent(
            query_mode="abstract_graph_query",
            target_node_types=["病证", "功效", "药材"],
            target_edge_types=["治疗病证", "具有功效"],
            requires_cypher_agent=True,
        )
    return QueryIntent(query_mode="entity_lookup")
