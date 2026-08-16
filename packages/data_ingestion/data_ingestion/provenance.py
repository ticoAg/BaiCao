"""数据集与图谱共用的溯源字段、prompt hash、同名合并键。"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord

GRAPH_NODE_PROPS = {
    "composition_text",
    "source_book",
    "alias",
    "skip_reason",
}
GRAPH_EDGE_PROPS = {"dosage"}
PROTECTED_EXISTING_PROPS = {
    "name",
    "id",
    "source",
    "latin_name",
    "pinyin_name",
    "status",
    "type",
    "dataset",
    "category",
    "description",
    "indications",
    "base_description",
    "verification_id",
    "verified_by",
    "verified_at",
    "imported_at",
}
DEFAULT_SCOPE_KEYS = {
    "daoyi-suyang": "manual:baicao-knowledge:daoyi-suyang",
}
DEFAULT_PROMPT_FILES = {
    "daoyi-suyang": Path(__file__).with_name("EXTRACT_SUYANG.md"),
}


def prompt_hash_for(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest[:12]}"


def scope_key_for(source_id: str) -> str:
    return DEFAULT_SCOPE_KEYS.get(source_id, f"manual:baicao-knowledge:{source_id}")


def lookup_names(node_type: str, node_name: str) -> list[str]:
    name = str(node_name).strip()
    names = [name]
    if node_type == "穴位":
        if name.endswith("穴") and len(name) > 1:
            names.append(name[:-1])
        elif not name.endswith("穴"):
            names.append(f"{name}穴")
    seen: set[str] = set()
    ordered: list[str] = []
    for item in names:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def slim_properties(properties: dict[str, Any] | None) -> dict[str, Any]:
    return {key: value for key, value in (properties or {}).items() if key in GRAPH_NODE_PROPS and value not in (None, "", [], {})}


def slim_edge(edge: DatasetEdge) -> DatasetEdge:
    props = {
        key: value
        for key, value in (edge.properties or {}).items()
        if key in GRAPH_EDGE_PROPS and value not in (None, "", [], {})
    }
    return DatasetEdge(type=edge.type, target=edge.target, properties=props)


def slim_record(
    record: DatasetRecord,
    *,
    prompt_hash: str,
    import_scope_key: str | None = None,
) -> DatasetRecord:
    scope = import_scope_key or record.import_scope_key or scope_key_for(record.source_id)
    properties = slim_properties(record.properties)
    if (record.properties or {}).get("skip_reason"):
        properties["skip_reason"] = record.properties["skip_reason"]
    return DatasetRecord(
        source_id=record.source_id,
        batch_id=record.batch_id,
        unit_id=record.unit_id,
        unit_title=None,
        processor=None,
        extracted_at=None,
        node_type=record.node_type,
        node_name=record.node_name,
        source=record.source_id,
        status="pending",
        evidence_refs=list(record.evidence_refs or []),
        evidence_text=record.evidence_text or None,
        prompt_hash=prompt_hash,
        import_scope_key=scope,
        properties=properties,
        edges=[slim_edge(edge) for edge in record.edges],
    )


def is_skip_record(record: DatasetRecord) -> bool:
    return (record.properties or {}).get("skip_reason") == "no_clinical_knowledge"


def graph_node_props(record: DatasetRecord) -> dict[str, Any]:
    props = slim_properties(record.properties)
    props.pop("skip_reason", None)
    if record.node_type == "证据" and record.evidence_text:
        props["evidence_text"] = record.evidence_text
    return props


def fill_if_empty(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    filled: dict[str, Any] = {}
    for key, value in incoming.items():
        if key in PROTECTED_EXISTING_PROPS:
            continue
        current = existing.get(key)
        if current in (None, "", [], {}) and value not in (None, "", [], {}):
            filled[key] = value
    return filled


def append_unique(values: list[str] | None, item: str | None) -> list[str]:
    items = list(values or [])
    if item and item not in items:
        items.append(item)
    return items
