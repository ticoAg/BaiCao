from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from knowledge_model.constants import EdgeType, NodeType

from ...kg.graph_metadata_service import graph_metadata_service

_ID_RULES = {
    "id_field": "标识",
    "name_field": "名称",
    "id_examples": ["formula-乌梅丸", "药材:黄芩"],
    "usage": (
        "search_nodes 用名称或标识定位；"
        "expand_neighbors 与 lookup_nodes 必须传「标识」，不要传名称；"
        "证据链常为 实体 -由证据支持-> 证据 -来源于-> 来源，需要 depth=2。"
    ),
}


def _enum_names(values: Iterable[Any]) -> list[str]:
    return [item.value for item in values]


async def build_graph_schema() -> dict[str, Any]:
    schema: dict[str, Any] = {
        **_ID_RULES,
        "labels": [{"name": name} for name in _enum_names(NodeType)],
        "relationship_types": [{"name": name} for name in _enum_names(EdgeType)],
        "source": "knowledge_model",
    }
    try:
        labels = await graph_metadata_service.list_labels(limit=50)
        rels = await graph_metadata_service.list_relationship_types(limit=80)
    except Exception:
        return schema

    live_labels = labels.get("items") if isinstance(labels, dict) else None
    live_rels = rels.get("items") if isinstance(rels, dict) else None
    if isinstance(live_labels, list) and live_labels:
        schema["labels"] = live_labels
        schema["source"] = "graph_metadata_service"
    if isinstance(live_rels, list) and live_rels:
        schema["relationship_types"] = live_rels
        schema["source"] = "graph_metadata_service"
    return schema
