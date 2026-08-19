from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SUPPORTED_BY = "由证据支持"
ORIGINATED_FROM = "来源于"
EVIDENCE_LABELS = frozenset({"证据", "Evidence"})
SOURCE_LABELS = frozenset({"来源", "Source"})
SNIPPET_KEYS = ("snippet", "evidence_text", "证据原文", "raw_text", "原文")


def citations_from_graph_state(graph_state: Mapping[str, Any] | None) -> list[dict[str, str]]:
    """从已收集子图生成 citation，不解析模型答案。"""
    if not graph_state:
        return []

    nodes_by_id = _index_nodes(graph_state.get("nodes"))
    source_by_from_id: dict[str, tuple[str, str]] = {}
    pairs: dict[tuple[str, str], dict[str, str]] = {}

    for edge in _values(graph_state.get("edges")):
        if not isinstance(edge, dict):
            continue
        rel_type = edge.get("rel_type") or edge.get("type")
        if rel_type == ORIGINATED_FROM:
            _collect_origin(edge, nodes_by_id, source_by_from_id)
        elif rel_type == SUPPORTED_BY:
            _collect_supported(edge, nodes_by_id, pairs)

    citations: list[dict[str, str]] = []
    for entity_id, evidence_id in pairs:
        citation = dict(pairs[(entity_id, evidence_id)])
        origin = source_by_from_id.get(entity_id) or source_by_from_id.get(evidence_id)
        if origin is not None:
            citation["source_id"] = origin[0]
            if origin[1]:
                citation["source_name"] = origin[1]
        citations.append(citation)

    citations.sort(key=lambda item: (item["evidence_id"], item["entity_id"]))
    return citations


def _values(container: Any) -> list[Any]:
    if isinstance(container, dict):
        return list(container.values())
    if isinstance(container, list):
        return list(container)
    return []


def _identity(node: Mapping[str, Any] | None) -> str | None:
    if not isinstance(node, Mapping):
        return None
    for key in ("id", "标识"):
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _endpoint_id(endpoint: Any) -> str | None:
    if isinstance(endpoint, str) and endpoint:
        return endpoint
    if isinstance(endpoint, Mapping):
        return _identity(endpoint)
    return None


def _labels(node: Mapping[str, Any] | None) -> set[str]:
    if not isinstance(node, Mapping):
        return set()
    found: set[str] = set()
    labels = node.get("labels")
    if isinstance(labels, list):
        found.update(str(item) for item in labels if item)
    elif isinstance(labels, str) and labels:
        found.add(labels)
    node_type = node.get("type")
    if isinstance(node_type, str) and node_type:
        found.add(node_type)
    return found


def _is_evidence(node: Mapping[str, Any] | None) -> bool:
    return bool(_labels(node) & EVIDENCE_LABELS)


def _is_source(node: Mapping[str, Any] | None) -> bool:
    return bool(_labels(node) & SOURCE_LABELS)


def _snippet(node: Mapping[str, Any] | None) -> str | None:
    if not isinstance(node, Mapping):
        return None
    for key in SNIPPET_KEYS:
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _display_name(node: Mapping[str, Any] | None) -> str:
    if not isinstance(node, Mapping):
        return ""
    for key in ("name", "名称"):
        value = node.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _index_nodes(container: Any) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for node in _values(container):
        if not isinstance(node, dict):
            continue
        node_id = _identity(node)
        if node_id:
            indexed[node_id] = node
    return indexed


def _lookup(
    nodes_by_id: Mapping[str, dict[str, Any]],
    endpoint: Any,
) -> tuple[str | None, dict[str, Any] | None]:
    endpoint_id = _endpoint_id(endpoint)
    if not endpoint_id:
        return None, None
    node = nodes_by_id.get(endpoint_id)
    return endpoint_id, node


def _collect_supported(
    edge: Mapping[str, Any],
    nodes_by_id: Mapping[str, dict[str, Any]],
    pairs: dict[tuple[str, str], dict[str, str]],
) -> None:
    source_id, source_node = _lookup(nodes_by_id, edge.get("source"))
    target_id, target_node = _lookup(nodes_by_id, edge.get("target"))
    if not source_id or not target_id:
        return

    if _is_evidence(target_node) and source_node is not None and not _is_evidence(source_node):
        entity_id, evidence_id, evidence_node = source_id, target_id, target_node
    elif _is_evidence(source_node) and target_node is not None and not _is_evidence(target_node):
        entity_id, evidence_id, evidence_node = target_id, source_id, source_node
    else:
        return

    if evidence_node is None:
        return
    snippet = _snippet(evidence_node)
    if not snippet:
        return
    key = (entity_id, evidence_id)
    if key in pairs:
        return
    pairs[key] = {
        "entity_id": entity_id,
        "evidence_id": evidence_id,
        "snippet": snippet,
    }


def _collect_origin(
    edge: Mapping[str, Any],
    nodes_by_id: Mapping[str, dict[str, Any]],
    source_by_from_id: dict[str, tuple[str, str]],
) -> None:
    source_id, source_node = _lookup(nodes_by_id, edge.get("source"))
    target_id, target_node = _lookup(nodes_by_id, edge.get("target"))
    if not source_id or not target_id:
        return

    if _is_source(target_node) and not _is_source(source_node):
        from_id, origin_id, origin_node = source_id, target_id, target_node
    elif _is_source(source_node) and not _is_source(target_node):
        from_id, origin_id, origin_node = target_id, source_id, source_node
    else:
        return

    if origin_node is None:
        return
    if from_id in source_by_from_id:
        return
    source_by_from_id[from_id] = (origin_id, _display_name(origin_node))
