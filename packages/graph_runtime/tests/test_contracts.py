from graph_runtime.contracts.inputs import GraphAskRequest, GraphExploreRequest
from graph_runtime.contracts.outputs import GraphAgentAnswer, GraphSubgraphMeta


def test_graph_ask_request_accepts_question_and_budget():
    request = GraphAskRequest(
        question="黄芩的功效和归经是什么？",
        max_depth=2,
        node_budget=30,
        allow_read_cypher=True,
    )

    assert request.question == "黄芩的功效和归经是什么？"
    assert request.max_depth == 2
    assert request.allow_read_cypher is True


def test_graph_explore_request_defaults_to_adaptive_mode():
    request = GraphExploreRequest(query="黄芩")

    assert request.query == "黄芩"
    assert request.mode == "adaptive"


def test_graph_agent_answer_exposes_dual_track_output():
    answer = GraphAgentAnswer(
        answer="黄芩味苦，性寒，归肺、胆、脾、胃、大肠、小肠经。",
        evidence=[
            {
                "node_id": "证据:1",
                "snippet": "【性味与归经】苦，寒。归肺、胆、脾、胃、大肠、小肠经。",
            }
        ],
        related_nodes=[{"id": "药材:黄芩", "name": "黄芩"}],
        related_edges=[{"source": "药材:黄芩", "target": "归经:肺经", "type": "归于经脉"}],
        subgraph_meta=GraphSubgraphMeta(center_node_id="药材:黄芩", actual_depth=1, fallback_used=False),
        reasoning_trace=[{"kind": "planner", "summary": "命中 schema 语义：功效、归经"}],
        tool_calls=[{"tool_name": "search_nodes", "summary": "召回黄芩"}],
    )

    assert answer.subgraph_meta.center_node_id == "药材:黄芩"
    assert answer.related_nodes[0]["name"] == "黄芩"


def test_graph_agent_answer_tool_calls_support_arguments_and_result_summary():
    answer = GraphAgentAnswer(
        answer="感冒相关中药包括桂枝、荆芥等。",
        evidence=[],
        related_nodes=[],
        related_edges=[],
        subgraph_meta=GraphSubgraphMeta(center_node_id=None, actual_depth=0, fallback_used=True),
        reasoning_trace=[{"kind": "planner", "summary": "识别为抽象症状问题"}],
        tool_calls=[
            {
                "tool_name": "graph_cypher_qa",
                "arguments": {
                    "question": "治感冒的中药都有哪些，怎么做",
                    "top_k": 8,
                },
                "summary": "使用 schema-aware cypher agent 查询图谱",
                "result_summary": "返回 6 个候选药材与 1 段结构化说明",
                "status": "completed",
            }
        ],
    )

    assert answer.tool_calls[0].tool_name == "graph_cypher_qa"
    assert answer.tool_calls[0].arguments["top_k"] == 8
    assert answer.tool_calls[0].result_summary.startswith("返回 6 个候选")


def test_graph_agent_answer_tool_calls_preserve_generated_cypher():
    answer = GraphAgentAnswer(
        answer="感冒相关中药包括桂枝、荆芥等。",
        evidence=[],
        related_nodes=[],
        related_edges=[],
        subgraph_meta=GraphSubgraphMeta(center_node_id=None, actual_depth=0, fallback_used=True),
        reasoning_trace=[{"kind": "planner", "summary": "识别为抽象症状问题"}],
        tool_calls=[
            {
                "tool_name": "graph_cypher_qa",
                "arguments": {
                    "question": "治感冒的中药都有哪些，怎么做",
                    "top_k": 8,
                    "generated_cypher": (
                        "MATCH (symptom:病证 {name: '感冒'})<-[:治疗病证]-(herb:中药) "
                        "RETURN herb.name LIMIT 8"
                    ),
                },
                "summary": "使用 schema-aware cypher agent 查询图谱",
                "result_summary": "返回 6 个候选药材与 1 段结构化说明",
                "status": "completed",
            }
        ],
    )

    assert "generated_cypher" in answer.tool_calls[0].arguments
    assert "MATCH (symptom:病证" in answer.tool_calls[0].arguments["generated_cypher"]
    assert not hasattr(answer.tool_calls[0], "generated_cypher")
