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
