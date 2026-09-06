"""入图载荷：数据集可保留来源于与原文片段，活图默认不写。"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from knowledge_model.constants import to_neo4j_label, to_neo4j_rel
from knowledge_model.graph_i18n import to_graph_properties

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.entity_identity import identity_key, stable_id_from_properties
from data_ingestion.provenance import fill_if_empty, graph_node_props, is_skip_record

SOURCE_EDGE_TYPE = "来源于"
EDGE_TARGET_TYPES: dict[str, tuple[str, ...]] = {
    "组成药材": ("药材", "饮片"),
    "适用于": ("病证",),
    "使用方剂": ("方剂",),
    "取用穴位": ("穴位",),
    "采用治法": ("治法",),
    "治疗病证": ("病证",),
    "关联药材": ("药材",),
    "关联治法": ("治法",),
    "关联证候": ("病证",),
    "关联症状": ("症状",),
    "记载于医案": ("医案",),
    "由证据支持": ("证据",),
    "来源于": ("来源",),
    "经过工艺": ("工艺",),
    "具有功效": ("功效",),
    "具有性味": ("性味",),
    "归于经脉": ("归经",),
    "具有饮片": ("饮片",),
    "相似于": ("药材", "方剂", "病证"),
    "包含成分": ("成分",),
}
FRAGMENT_KEYS = frozenset(
    {
        "evidence_text",
        "证据原文",
        "raw_text",
        "原文",
        "source_text",
        "content",
        "text",
        "snippet",
    }
)


def for_graph_store(
    record: DatasetRecord, *, include_source_graph: bool = False
) -> DatasetRecord:
    if include_source_graph:
        return record
    properties = {
        key: value
        for key, value in (record.properties or {}).items()
        if key not in FRAGMENT_KEYS
    }
    return record.model_copy(
        update={
            "evidence_text": None,
            "properties": properties,
            "edges": [edge for edge in record.edges if edge.type != SOURCE_EDGE_TYPE],
        }
    )


def omit_from_graph(record: DatasetRecord, *, include_source_graph: bool = False) -> bool:
    if is_skip_record(record):
        return True
    return not include_source_graph and record.node_type == "来源"


def graph_store_records(
    records: list[DatasetRecord], *, include_source_graph: bool = False
) -> tuple[list[DatasetRecord], Counter]:
    stats: Counter = Counter()
    kept: list[DatasetRecord] = []
    for record in records:
        stats["source_edges"] += sum(1 for edge in record.edges if edge.type == SOURCE_EDGE_TYPE)
        if record.evidence_text:
            stats["fragment_records"] += 1
        payload = for_graph_store(record, include_source_graph=include_source_graph)
        if omit_from_graph(payload, include_source_graph=include_source_graph):
            stats["omitted_records"] += 1
            continue
        kept.append(payload)
        stats["graph_records"] += 1
        stats["graph_edges"] += len(payload.edges)
    collapsed = collapse_dataset_records(kept)
    stats["collapsed_records"] = len(kept) - len(collapsed)
    stats["graph_records"] = len(collapsed)
    stats["graph_edges"] = sum(len(record.edges) for record in collapsed)
    return collapsed, stats


def collapse_dataset_records(records: list[DatasetRecord]) -> list[DatasetRecord]:
    merged: dict[tuple[str, str, str], DatasetRecord] = {}
    order: list[tuple[str, str, str]] = []
    for record in records:
        key = identity_key(
            record.node_type, record.node_name, stable_id_from_properties(record.properties)
        )
        existing = merged.get(key)
        if existing is None:
            merged[key] = record
            order.append(key)
            continue
        merged[key] = _merge_records(existing, record)
    return [merged[key] for key in order]


def _merge_records(existing: DatasetRecord, incoming: DatasetRecord) -> DatasetRecord:
    properties = dict(existing.properties or {})
    for key, value in fill_if_empty(properties, incoming.properties or {}).items():
        properties[key] = value
    edges = list(existing.edges)
    seen = {_edge_key(edge) for edge in edges}
    for edge in incoming.edges:
        marker = _edge_key(edge)
        if marker not in seen:
            edges.append(edge)
            seen.add(marker)
    return existing.model_copy(update={"properties": properties, "edges": edges})


def _edge_key(edge: DatasetEdge) -> tuple[str, str, str]:
    return (
        edge.type,
        edge.target,
        json.dumps(edge.properties or {}, sort_keys=True, ensure_ascii=False),
    )


def node_admin_id(record: DatasetRecord) -> str:
    stable = stable_id_from_properties(record.properties)
    label = to_neo4j_label(record.node_type)
    if stable:
        return f"{label}:{record.node_name}:{stable}"
    return f"{label}:{record.node_name}"


def write_admin_csvs(
    records: list[DatasetRecord],
    output_dir: Path,
    *,
    include_source_graph: bool = False,
) -> dict[str, Any]:
    graph_records, stats = graph_store_records(
        records, include_source_graph=include_source_graph
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    nodes_dir = output_dir / "nodes"
    rels_dir = output_dir / "rels"
    nodes_dir.mkdir(exist_ok=True)
    rels_dir.mkdir(exist_ok=True)
    by_label: dict[str, list[DatasetRecord]] = defaultdict(list)
    id_by_type_name: dict[tuple[str, str], str] = {}
    for record in graph_records:
        label = to_neo4j_label(record.node_type)
        by_label[label].append(record)
        id_by_type_name.setdefault((record.node_type, record.node_name), node_admin_id(record))

    node_files: list[str] = []
    for label, group in sorted(by_label.items()):
        keys: list[str] = []
        rows: list[dict[str, Any]] = []
        for record in group:
            props = to_graph_properties(
                {
                    "name": record.node_name,
                    "id": node_admin_id(record),
                    "source": record.source_id,
                    "status": "pending",
                    "import_source_id": record.source_id,
                    "import_batch_id": record.batch_id,
                    "import_scope_key": record.import_scope_key,
                    "prompt_hash": record.prompt_hash,
                    "import_source_ids": [record.source_id],
                    "import_batch_ids": [record.batch_id],
                    "import_scope_keys": [record.import_scope_key],
                    "prompt_hashes": [record.prompt_hash],
                    **graph_node_props(record),
                }
            )
            row = {key: _csv_value(value) for key, value in props.items() if _csv_value(value) is not None}
            row[":ID"] = node_admin_id(record)
            row[":LABEL"] = label
            rows.append(row)
            for key in row:
                if key not in keys:
                    keys.append(key)
        path = nodes_dir / f"{label}.csv"
        _write_csv(path, keys, rows)
        node_files.append(f'--nodes="${{ROOT}}/{path.relative_to(output_dir).as_posix()}"')

    rel_files: list[str] = []
    grouped_edges: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    dangling = 0
    for record in graph_records:
        source_label = to_neo4j_label(record.node_type)
        source_id = node_admin_id(record)
        for edge in record.edges:
            target_id, target_label = _resolve_admin_target(edge, id_by_type_name)
            if target_id is None or target_label is None:
                dangling += 1
                continue
            localized = to_graph_properties(
                {
                    "import_source_id": record.source_id,
                    "import_batch_id": record.batch_id,
                    "import_unit_id": record.unit_id,
                    "import_scope_key": record.import_scope_key,
                    "prompt_hash": record.prompt_hash,
                    **(edge.properties or {}),
                }
            )
            grouped_edges[(source_label, to_neo4j_rel(edge.type), target_label)].append(
                {
                    ":START_ID": source_id,
                    ":END_ID": target_id,
                    ":TYPE": to_neo4j_rel(edge.type),
                    **{key: _csv_value(value) for key, value in localized.items() if _csv_value(value) is not None},
                }
            )
    for (source_label, rel, target_label), rows in sorted(grouped_edges.items()):
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        path = rels_dir / f"{source_label}-{rel}-{target_label}.csv"
        _write_csv(path, keys, rows)
        rel_files.append(
            f'--relationships="${{ROOT}}/{path.relative_to(output_dir).as_posix()}"'
        )

    command = [
        "/var/lib/neo4j/bin/neo4j-admin",
        "database",
        "import",
        "full",
        "neo4j",
        "--overwrite-destination=true",
        "--id-type=STRING",
        "--multiline-fields=true",
        *node_files,
        *rel_files,
    ]
    script_path = output_dir / "neo4j-admin.sh"
    script_path.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "# 停 Neo4j 后把本目录挂到容器 /import，用 neo4j:5-community 执行本脚本。\n"
        "# 命令见 docs/architecture/knowledge-dataset.md\n"
        'ROOT="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"\n'
        + " \\\n  ".join(command)
        + "\n",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    stats["dangling_edges"] = dangling
    stats["node_files"] = len(node_files)
    stats["rel_files"] = len(rel_files)
    stats["output_dir"] = str(output_dir)
    return dict(stats)


def _resolve_admin_target(
    edge: DatasetEdge, id_by_type_name: dict[tuple[str, str], str]
) -> tuple[str | None, str | None]:
    target_types = EDGE_TARGET_TYPES.get(edge.type)
    if target_types is None:
        return None, None
    for target_type in target_types:
        node_id = id_by_type_name.get((target_type, edge.target))
        if node_id:
            return node_id, to_neo4j_label(target_type)
    return None, None


def _csv_value(value: Any) -> str | None:
    if value in (None, "", [], {}):
        return None
    if isinstance(value, dict):
        return None
    if isinstance(value, list):
        return ";".join(str(item).replace(";", " ") for item in value if item not in (None, ""))
    return str(value)


def _write_csv(path: Path, keys: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in keys})
