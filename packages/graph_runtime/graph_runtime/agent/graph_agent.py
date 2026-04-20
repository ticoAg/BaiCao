from graph_runtime.contracts.outputs import GraphAgentAnswer, GraphSubgraphMeta
from graph_runtime.planner.plan_builder import build_graph_plan
from graph_runtime.primitives.evidence import collect_evidence_snippets

from .answer_synthesis import synthesize_answer
from .exploration_policy import choose_exploration_depth


class GraphExplorationAgent:
    def __init__(self, graph_facade) -> None:
        self.graph_facade = graph_facade

    async def ask(self, request) -> GraphAgentAnswer:
        plan = build_graph_plan(request.question)
        tool_calls = []

        matches = await self.graph_facade.search_nodes(request.question, limit=5)
        tool_calls.append({"tool_name": "search_nodes", "summary": f"召回 {len(matches)} 个候选"})

        center = matches[0] if matches else None
        exploration_depth = choose_exploration_depth(plan, request.max_depth)
        subgraph = (
            await self.graph_facade.expand_neighbors(
                center["id"], depth=exploration_depth, limit=request.node_budget
            )
            if center
            else {"center": None, "nodes": [], "edges": []}
        )
        tool_calls.append({"tool_name": "expand_neighbors", "summary": "展开中心节点邻居"})

        related_nodes = subgraph.get("nodes", [])
        related_edges = subgraph.get("edges", [])
        answer = synthesize_answer(request.question, center, related_nodes, related_edges, plan)
        evidence = collect_evidence_snippets(related_nodes)

        return GraphAgentAnswer(
            answer=answer,
            evidence=evidence,
            related_nodes=related_nodes,
            related_edges=related_edges,
            subgraph_meta=GraphSubgraphMeta(
                center_node_id=center["id"] if center else None,
                actual_depth=exploration_depth if center else 0,
                fallback_used=False,
                node_count=len(related_nodes),
                edge_count=len(related_edges),
            ),
            reasoning_trace=[
                {
                    "kind": "planner",
                    "summary": f"schema targets: {plan['target_node_types']} / {plan['target_edge_types']}",
                }
            ],
            tool_calls=tool_calls,
        )
