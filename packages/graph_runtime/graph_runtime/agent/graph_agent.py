from collections import deque
from dataclasses import dataclass
from typing import Any

from graph_runtime.contracts.outputs import GraphAgentAnswer, GraphSubgraphMeta
from graph_runtime.contracts.tool_calls import GraphToolCall
from graph_runtime.planner.plan_builder import build_graph_plan
from graph_runtime.primitives.evidence import collect_evidence_snippets

from .answer_synthesis import synthesize_answer
from .exploration_policy import choose_exploration_depth


@dataclass
class PlannedToolCall:
    tool_name: str
    arguments: dict[str, Any]
    summary: str


class GraphExplorationAgent:
    def __init__(self, graph_facade) -> None:
        self.graph_facade = graph_facade

    async def ask(self, request) -> GraphAgentAnswer:
        plan = build_graph_plan(request.question)
        tool_calls: list[GraphToolCall] = []
        reasoning_trace = [
            {
                "kind": "planner",
                "summary": f"schema targets: {plan['target_node_types']} / {plan['target_edge_types']}",
            }
        ]

        exploration_depth = choose_exploration_depth(plan, request.max_depth)
        pending_calls = deque(self._build_initial_tool_calls(plan))
        searched_queries: set[str] = set()
        expanded_node_ids: set[str] = set()
        fallback_attempted = False
        fallback_used = False
        center: dict | None = None
        subgraph: dict[str, Any] = {"center": None, "nodes": [], "edges": []}
        fallback_name: str | None = None

        while pending_calls and len(tool_calls) < request.tool_call_budget:
            planned_call = pending_calls.popleft()
            tool_call, result = await self._execute_tool_call(planned_call)
            tool_calls.append(tool_call)

            if planned_call.tool_name == "search_nodes":
                query = str(planned_call.arguments.get("query", ""))
                searched_queries.add(query)
                matches = result if isinstance(result, list) else []
                if matches and center is None:
                    center = self._select_center_node(matches)
                    if center and center.get("id") not in expanded_node_ids:
                        pending_calls.appendleft(
                            PlannedToolCall(
                                tool_name="expand_neighbors",
                                arguments={
                                    "node_id": center["id"],
                                    "depth": exploration_depth,
                                    "limit": request.node_budget,
                                },
                                summary="根据命中中心节点展开邻居子图",
                            )
                        )
                elif (
                    not matches
                    and center is None
                    and not any(call.tool_name == "search_nodes" for call in pending_calls)
                    and request.allow_read_cypher
                    and not fallback_attempted
                ):
                    fallback_attempted = True
                    pending_calls.append(
                        PlannedToolCall(
                            tool_name="read_cypher",
                            arguments={
                                "query": self._build_readonly_fallback_cypher(query or plan["normalized_question"])
                            },
                            summary="图谱搜索未命中，尝试只读 Cypher fallback",
                        )
                    )

            elif planned_call.tool_name == "expand_neighbors":
                if isinstance(result, dict):
                    subgraph = result
                    if result.get("center"):
                        center = result["center"]
                    if center and center.get("id"):
                        expanded_node_ids.add(center["id"])

            elif planned_call.tool_name == "read_cypher":
                fallback_used = True
                fallback_name = self._extract_fallback_name(result)
                if fallback_name and fallback_name not in searched_queries:
                    pending_calls.appendleft(
                        PlannedToolCall(
                            tool_name="search_nodes",
                            arguments={"query": fallback_name, "limit": 5},
                            summary="根据只读 Cypher 候选回查图谱节点",
                        )
                    )

            if center and subgraph.get("nodes"):
                break

        related_nodes = subgraph.get("nodes", [])
        related_edges = subgraph.get("edges", [])
        answer = synthesize_answer(request.question, center, related_nodes, related_edges, plan)
        evidence = collect_evidence_snippets(related_nodes)
        reasoning_trace.append(
            {
                "kind": "tool_loop",
                "summary": f"执行 {len(tool_calls)} 次图谱工具调用并产出最终答案",
            }
        )
        if fallback_name:
            reasoning_trace.append(
                {
                    "kind": "fallback",
                    "summary": f"只读 Cypher 提供候选节点：{fallback_name}",
                }
            )

        return GraphAgentAnswer(
            answer=answer,
            evidence=evidence,
            related_nodes=related_nodes,
            related_edges=related_edges,
            subgraph_meta=GraphSubgraphMeta(
                center_node_id=center["id"] if center else None,
                actual_depth=exploration_depth if center else 0,
                fallback_used=fallback_used,
                node_count=len(related_nodes),
                edge_count=len(related_edges),
            ),
            reasoning_trace=reasoning_trace,
            tool_calls=tool_calls,
        )

    def _build_initial_tool_calls(self, plan: dict) -> list[PlannedToolCall]:
        queries = [
            candidate
            for candidate in plan.get("entity_hints", [])
            if isinstance(candidate, str) and candidate.strip()
        ]
        if not queries:
            queries = [plan["normalized_question"]]
        return [
            PlannedToolCall(
                tool_name="search_nodes",
                arguments={"query": query, "limit": 5},
                summary="根据问题解析候选实体并搜索图谱节点",
            )
            for query in queries
        ]

    async def _execute_tool_call(self, planned_call: PlannedToolCall) -> tuple[GraphToolCall, Any]:
        if planned_call.tool_name == "search_nodes":
            result = await self.graph_facade.search_nodes(
                planned_call.arguments["query"],
                limit=int(planned_call.arguments.get("limit", 20)),
            )
            return (
                GraphToolCall(
                    tool_name="search_nodes",
                    arguments=planned_call.arguments,
                    summary=planned_call.summary,
                    result_summary=f"命中 {len(result)} 个候选",
                ),
                result,
            )

        if planned_call.tool_name == "expand_neighbors":
            result = await self.graph_facade.expand_neighbors(
                planned_call.arguments["node_id"],
                depth=int(planned_call.arguments.get("depth", 1)),
                limit=int(planned_call.arguments.get("limit", 20)),
            )
            return (
                GraphToolCall(
                    tool_name="expand_neighbors",
                    arguments=planned_call.arguments,
                    summary=planned_call.summary,
                    result_summary=(
                        f"返回 {len(result.get('nodes', []))} 个节点 / {len(result.get('edges', []))} 条关系"
                    ),
                ),
                result,
            )

        if planned_call.tool_name == "read_cypher":
            result = await self.graph_facade.read_cypher(planned_call.arguments["query"])
            return (
                GraphToolCall(
                    tool_name="read_cypher",
                    arguments=planned_call.arguments,
                    summary=planned_call.summary,
                    result_summary=f"返回 {len(result)} 行只读结果",
                ),
                result,
            )

        raise ValueError(f"Unsupported graph tool: {planned_call.tool_name}")

    def _select_center_node(self, matches: list[dict]) -> dict | None:
        return matches[0] if matches else None

    def _build_readonly_fallback_cypher(self, query_text: str) -> str:
        escaped = query_text.replace("\\", "\\\\").replace('"', '\\"')
        if escaped:
            return f'MATCH (n) WHERE n.name CONTAINS "{escaped}" RETURN n.name AS name LIMIT 5'
        return "MATCH (n) RETURN n.name AS name LIMIT 5"

    def _extract_fallback_name(self, rows: Any) -> str | None:
        if not isinstance(rows, list):
            return None
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("name") or row.get("node_name")
            if name:
                return str(name)
        return None
