"""数据集记录信封：每条结构化结果必须带 source_id 与 batch_id。"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from knowledge_model.constants import EdgeType, NodeType

ALLOWED_NODE_TYPES = {item.value for item in NodeType}
ALLOWED_EDGE_TYPES = {item.value for item in EdgeType}


class DatasetEdge(BaseModel):
    type: str
    target: str
    properties: dict[str, Any] = Field(default_factory=dict)


class DatasetRecord(BaseModel):
    source_id: str
    batch_id: str
    unit_id: str
    unit_title: str | None = None
    processor: str | None = None
    extracted_at: str | None = None
    node_type: str
    node_name: str
    source: str | None = None
    status: str = "pending"
    evidence_refs: list[str] = Field(default_factory=list)
    evidence_text: str | None = None
    prompt_hash: str | None = None
    import_scope_key: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    edges: list[DatasetEdge] = Field(default_factory=list)

    def validate_types(self) -> None:
        if self.node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(f"unsupported node_type: {self.node_type}")
        for edge in self.edges:
            if edge.type not in ALLOWED_EDGE_TYPES:
                raise ValueError(f"unsupported edge type: {edge.type}")


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stamp_import_record(
    raw: dict[str, Any],
    *,
    source_id: str,
    batch_id: str,
    unit_id: str,
    processor: str,
    unit_title: str | None = None,
    extracted_at: str | None = None,
    prompt_hash: str | None = None,
    import_scope_key: str | None = None,
) -> DatasetRecord:
    properties = dict(raw.get("properties") or {})
    properties.setdefault("import_source_id", source_id)
    properties.setdefault("import_batch_id", batch_id)
    properties.setdefault("import_unit_id", unit_id)
    record = DatasetRecord(
        source_id=source_id,
        batch_id=batch_id,
        unit_id=unit_id,
        unit_title=unit_title,
        processor=processor,
        extracted_at=extracted_at or utc_now(),
        node_type=str(raw.get("node_type") or ""),
        node_name=str(raw.get("node_name") or ""),
        source=str(raw.get("source") or source_id),
        status=str(raw.get("status") or "pending"),
        evidence_refs=list(raw.get("evidence_refs") or []),
        evidence_text=raw.get("evidence_text"),
        prompt_hash=prompt_hash or raw.get("prompt_hash"),
        import_scope_key=import_scope_key or raw.get("import_scope_key"),
        properties=properties,
        edges=[DatasetEdge.model_validate(edge) for edge in raw.get("edges") or []],
    )
    record.validate_types()
    return record


def compute_stats(records: list[DatasetRecord]) -> dict[str, Any]:
    node_counts = Counter(record.node_type for record in records)
    edge_counts: Counter[str] = Counter()
    units = {(record.source_id, record.unit_id) for record in records}
    batches = sorted({record.batch_id for record in records})
    by_batch: dict[str, dict[str, Any]] = {}
    for batch_id in batches:
        batch_records = [record for record in records if record.batch_id == batch_id]
        batch_nodes = Counter(record.node_type for record in batch_records)
        batch_edges: Counter[str] = Counter()
        for record in batch_records:
            edge_counts.update(edge.type for edge in record.edges)
            batch_edges.update(edge.type for edge in record.edges)
        by_batch[batch_id] = {
            "record_count": len(batch_records),
            "unit_count": len({record.unit_id for record in batch_records}),
            "node_type_counts": dict(batch_nodes),
            "edge_type_counts": dict(batch_edges),
        }
    source_ids = sorted({record.source_id for record in records})
    prompt_hashes = sorted({record.prompt_hash for record in records if record.prompt_hash})
    return {
        "generated_at": utc_now(),
        "source_ids": source_ids,
        "batch_ids": batches,
        "prompt_hashes": prompt_hashes,
        "record_count": len(records),
        "unit_count": len(units),
        "node_type_counts": dict(node_counts),
        "edge_type_counts": dict(edge_counts),
        "by_batch": by_batch,
    }
