from __future__ import annotations

import ast
import json
from typing import Any


def base_final_payload(session_id: str, turn_id: str) -> dict[str, Any]:
    return {
        "answer": "",
        "provider_reasoning": [],
        "tool_calls": [],
        "related_nodes": [],
        "related_edges": [],
        "subgraph_meta": {
            "center_node_id": None,
            "actual_depth": 0,
            "fallback_used": False,
            "node_count": 0,
            "edge_count": 0,
        },
        "evidence": [],
        "reasoning_trace": [],
        "session_id": session_id,
        "turn_id": turn_id,
    }


def parse_tool_payload(value: Any) -> Any:
    if isinstance(value, dict) and value.get("type") == "text" and isinstance(value.get("text"), str):
        return parse_tool_payload(value["text"])

    if isinstance(value, (dict, list)):
        return value

    if not isinstance(value, str):
        return value

    text = value.strip()
    if not text:
        return ""

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if text.startswith(("{", "[")):
        try:
            return ast.literal_eval(text)
        except (SyntaxError, ValueError):
            pass

    return text


def _coerce_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _node_id(node: dict[str, Any]) -> str | None:
    for key in ("id", "标识", "name"):
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _edge_id(edge: dict[str, Any]) -> str | None:
    edge_id = edge.get("id")
    if isinstance(edge_id, str) and edge_id:
        return edge_id

    source = edge.get("source")
    target = edge.get("target")
    rel_type = edge.get("rel_type") or edge.get("type") or "related"

    source_id = source if isinstance(source, str) else source.get("id") if isinstance(source, dict) else None
    target_id = target if isinstance(target, str) else target.get("id") if isinstance(target, dict) else None
    if isinstance(source_id, str) and isinstance(target_id, str):
        return f"{source_id}:{rel_type}:{target_id}"
    return None


def merge_graph_patch(
    graph_state: dict[str, Any],
    patch: dict[str, Any] | None,
    *,
    tool_arguments: dict[str, Any] | None = None,
) -> None:
    if not patch:
        return

    for node in patch.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_key = _node_id(node)
        if not node_key:
            continue
        graph_state["nodes"][node_key] = node

    for edge in patch.get("edges", []):
        if not isinstance(edge, dict):
            continue
        edge_key = _edge_id(edge)
        if not edge_key:
            continue
        graph_state["edges"][edge_key] = edge

    center_node_id = patch.get("center_node_id")
    if isinstance(center_node_id, str) and center_node_id:
        graph_state["center_node_id"] = center_node_id

    depth = tool_arguments.get("depth") if isinstance(tool_arguments, dict) else None
    if isinstance(depth, int):
        graph_state["actual_depth"] = max(graph_state["actual_depth"], depth)


def _items_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return _coerce_dict_list(payload["items"])
    return _coerce_dict_list(payload)


def patch_from_tool_payload(tool_name: str, payload: Any) -> dict[str, Any] | None:
    if tool_name in {"search_nodes", "lookup_nodes"}:
        nodes = _items_from_payload(payload)
        if nodes:
            return {"nodes": nodes}
        return None

    if tool_name == "expand_neighbors" and isinstance(payload, dict):
        center = payload.get("center")
        center_node_id = None
        if isinstance(center, dict):
            center_node_id = _node_id(center)
        elif isinstance(payload.get("center_node_id"), str):
            center_node_id = payload["center_node_id"]
        return {
            "nodes": _coerce_dict_list(payload.get("nodes")),
            "edges": _coerce_dict_list(payload.get("edges")),
            "center_node_id": center_node_id,
        }

    if tool_name == "search_edges":
        edges = _items_from_payload(payload)
        nodes: list[dict[str, Any]] = []
        for edge in edges:
            for endpoint_key in ("source", "target"):
                endpoint = edge.get(endpoint_key)
                if isinstance(endpoint, dict):
                    nodes.append(endpoint)
        if edges or nodes:
            return {"nodes": nodes, "edges": edges}
        return None

    return None


def summarize_tool_payload(tool_name: str, payload: Any) -> str:
    if isinstance(payload, dict) and isinstance(payload.get("count"), int):
        if tool_name in {"search_nodes", "lookup_nodes"}:
            return f"返回 {payload['count']} 个节点"
        if tool_name == "search_edges":
            return f"返回 {payload['count']} 条关系"
        if tool_name == "expand_neighbors":
            node_count = payload.get("node_count")
            edge_count = payload.get("edge_count")
            if isinstance(node_count, int) and isinstance(edge_count, int):
                return f"返回 {node_count} 个节点、{edge_count} 条关系"
    if tool_name in {"search_nodes", "lookup_nodes"} and isinstance(payload, list):
        return f"返回 {len(payload)} 个节点"
    if tool_name == "search_edges" and isinstance(payload, list):
        return f"返回 {len(payload)} 条关系"
    if tool_name == "expand_neighbors" and isinstance(payload, dict):
        node_count = len(_coerce_dict_list(payload.get("nodes")))
        edge_count = len(_coerce_dict_list(payload.get("edges")))
        return f"返回 {node_count} 个节点、{edge_count} 条关系"
    if isinstance(payload, list):
        return f"返回 {len(payload)} 条记录"
    if isinstance(payload, dict):
        keys = ", ".join(sorted(payload.keys())[:4])
        return f"返回对象：{keys}" if keys else "返回对象结果"
    if isinstance(payload, str):
        snippet = payload.strip()
        return snippet[:80] if snippet else "工具已完成"
    return "工具已完成"


def payload_preview(payload: Any) -> dict[str, Any] | None:
    if isinstance(payload, dict):
        return payload
    return None
