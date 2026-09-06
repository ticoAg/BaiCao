from __future__ import annotations

from typing import Any

EMPTY_NODE_HINT = (
    "未命中节点。可换中文「名称」、改用精确「标识」，或加上 label（药材/方剂/医案/穴位/治法）。"
)
EMPTY_EDGE_HINT = (
    "未命中关系。关系名用中文，例如 组成药材、使用方剂、由证据支持、来源于；可加 source_label / target_label。"
)
MISSING_NODE_HINT = "未找到该标识。请先 search_nodes，使用返回项里的「标识」或 id 再 expand / lookup。"
NO_NEIGHBOR_HINT = "当前深度没有邻居。证据的「来源于」通常在第 2 跳，可将 depth 设为 2。"


def wrap_node_items(items: Any) -> dict[str, Any]:
    rows = [item for item in items] if isinstance(items, list) else []
    payload: dict[str, Any] = {"count": len(rows), "items": rows}
    if not rows:
        payload["hint"] = EMPTY_NODE_HINT
    return payload


def wrap_edge_items(items: Any) -> dict[str, Any]:
    rows = [item for item in items] if isinstance(items, list) else []
    payload: dict[str, Any] = {"count": len(rows), "items": rows}
    if not rows:
        payload["hint"] = EMPTY_EDGE_HINT
    return payload


def wrap_expand_subgraph(result: Any) -> dict[str, Any]:
    source = dict(result) if isinstance(result, dict) else {}
    raw_nodes = source.get("nodes")
    raw_edges = source.get("edges")
    nodes = (
        [item for item in raw_nodes if isinstance(item, dict)]
        if isinstance(raw_nodes, list)
        else []
    )
    edges = (
        [item for item in raw_edges if isinstance(item, dict)]
        if isinstance(raw_edges, list)
        else []
    )
    payload: dict[str, Any] = {
        "center": source.get("center"),
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
    if payload.get("center") is None:
        payload["hint"] = MISSING_NODE_HINT
    elif not edges:
        payload["hint"] = NO_NEIGHBOR_HINT
    return payload

