from dataclasses import dataclass


@dataclass
class PlannedToolCall:
    tool_name: str
    arguments: dict
    summary: str


def build_initial_tool_plan(plan: dict) -> list[PlannedToolCall]:
    if plan["query_mode"] == "abstract_graph_query":
        return [
            PlannedToolCall(
                tool_name="graph_cypher_qa",
                arguments={"question": plan["question"], "top_k": 8},
                summary="对抽象问题使用 schema-aware graph cypher agent",
            )
        ]

    query = plan["entity_hints"][0] if plan["entity_hints"] else plan["normalized_question"]
    return [
        PlannedToolCall(
            tool_name="search_nodes",
            arguments={"query": query, "limit": 5},
            summary="根据实体 hint 搜索图谱节点",
        )
    ]
