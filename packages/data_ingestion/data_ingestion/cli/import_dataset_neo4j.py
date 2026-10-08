"""把数据集折叠成规范名 CSV，默认交给 neo4j-admin 空库导入。

`--mode admin`（默认）不连库，只写 CSV 与 neo4j-admin.sh。
`--mode bolt` 才对运行中的库 UNWIND，仅用于增量。
`--mode indexes` 只给已有库补名称索引。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import batched
from pathlib import Path
from typing import Any

from graph_schema.constants import NodeType, to_neo4j_label, to_neo4j_rel
from graph_schema.graph_i18n import to_graph_properties

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.entity_identity import GRAPH_FIND_KEYS, chinese_lookup_values
from data_ingestion.graph_store_payload import EDGE_TARGET_TYPES, graph_store_records, write_admin_csvs
from data_ingestion.provenance import (
    append_unique,
    fill_if_empty,
    graph_node_props,
    lookup_names,
    prompt_hash_for,
    slim_record,
    DEFAULT_PROMPT_FILES,
)

DEFAULT_BATCH_SIZE = 2000
MAX_BATCH_SIZE = 10000
EVIDENCE_UNWIND_SIZE = 1000


def load_jsonl(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = DatasetRecord.model_validate(json.loads(line))
            record.validate_types()
            records.append(record)
    return records


def load_parquet_records(records_path: Path, edges_path: Path | None = None) -> list[DatasetRecord]:
    import pyarrow.parquet as pq

    from data_ingestion.cli.export_dataset_parquet import records_from_tables

    edge_file = edges_path or records_path.with_name("edges.parquet")
    if not edge_file.is_file():
        raise SystemExit(f"parquet import needs edges file: {edge_file}")
    return records_from_tables(pq.read_table(records_path), pq.read_table(edge_file))


def load_dataset_parquet(dataset_root: Path, *, tier: str = "all") -> list[DatasetRecord]:
    from data_ingestion.dataset_catalog import RELEASE_PUBLIC, RELEASE_RESTRICTED

    if tier == "all":
        tiers = (RELEASE_PUBLIC, RELEASE_RESTRICTED)
    else:
        tiers = (tier,)
    records: list[DatasetRecord] = []
    for name in tiers:
        path = dataset_root / "data" / name / "records.parquet"
        if path.is_file():
            records.extend(load_parquet_records(path))
    return records


def load_import_records(
    *,
    records_path: Path | None = None,
    edges_path: Path | None = None,
    dataset_root: Path | None = None,
    tier: str = "all",
) -> list[DatasetRecord]:
    if dataset_root is not None:
        return load_dataset_parquet(dataset_root, tier=tier)
    if records_path is None:
        raise SystemExit("pass --records or --dataset-root")
    if records_path.suffix == ".parquet":
        return load_parquet_records(records_path, edges_path)
    return load_jsonl(records_path)


def prepare_import_records(
    records: list[DatasetRecord], *, prompt_file: Path | None = None
) -> list[DatasetRecord]:
    fallback_by_source: dict[str, str] = {}
    source_ids = {record.source_id for record in records}

    def prompt_hash_for_record(record: DatasetRecord) -> str:
        if record.prompt_hash:
            return record.prompt_hash
        if record.source_id not in fallback_by_source:
            path = prompt_file if len(source_ids) == 1 else None
            path = path or DEFAULT_PROMPT_FILES.get(record.source_id)
            if path is None or not path.is_file():
                raise SystemExit(
                    f"records missing prompt_hash for {record.source_id}; pass --prompt-file"
                )
            fallback_by_source[record.source_id] = prompt_hash_for(path)
        return fallback_by_source[record.source_id]

    return [
        slim_record(
            record,
            prompt_hash=prompt_hash_for_record(record),
            import_scope_key=record.import_scope_key,
        )
        for record in records
    ]


def clamp_batch_size(value: int) -> int:
    if value < 1:
        raise ValueError("batch-size must be >= 1")
    return min(value, MAX_BATCH_SIZE)


def _lookup_values(props: dict[str, Any]) -> list[str]:
    return chinese_lookup_values(props)


def _record_lookup_names(record: DatasetRecord) -> list[str]:
    names = lookup_names(record.node_type, record.node_name)
    for alias in chinese_lookup_values(record.properties):
        names = append_unique(names, alias)
    return names


def _import_meta(record: DatasetRecord) -> dict[str, Any]:
    return {
        "source_id": to_graph_properties({"import_source_id": record.source_id})["导入源"],
        "batch_id": record.batch_id,
        "scope": to_graph_properties({"import_scope_key": record.import_scope_key or ""})["导入范围键"],
        "prompt_hash": record.prompt_hash,
    }


def _create_node_props(record: DatasetRecord) -> dict[str, Any]:
    return to_graph_properties(
        {
            "name": record.node_name,
            "source": record.source_id,
            "status": "pending",
            "import_source_id": record.source_id,
            "import_batch_id": record.batch_id,
            "import_unit_id": record.unit_id,
            "import_scope_key": record.import_scope_key,
            "prompt_hash": record.prompt_hash,
            "import_source_ids": [record.source_id],
            "import_batch_ids": [record.batch_id],
            "import_scope_keys": [record.import_scope_key],
            "prompt_hashes": [record.prompt_hash],
            **graph_node_props(record),
        }
    )


def _filled_props(existing_props: dict[str, Any], record: DatasetRecord) -> dict[str, Any]:
    existing_en = {
        **existing_props,
        **{
            en: existing_props[zh]
            for zh, en in {"名称": "name"}.items()
            if zh in existing_props
        },
    }
    return to_graph_properties(fill_if_empty(existing_en, graph_node_props(record)))


def _append_prop_list(props: dict[str, Any], key: str, value: Any) -> None:
    if value in (None, ""):
        return
    current = list(props.get(key) or [])
    if value not in current:
        current.append(value)
        props[key] = current


def _unwind_size(label: str, batch_size: int) -> int:
    if label == "证据":
        return min(batch_size, EVIDENCE_UNWIND_SIZE)
    return batch_size


class NodeCache:
    """预加载已有节点，避免每条记录两次全表扫描。不在事务内写入，以免重试留下脏 elementId。"""

    def __init__(self) -> None:
        self.by_label_name: dict[tuple[str, str], dict[str, Any]] = {}
        self.by_label_alias: dict[tuple[str, str], str] = {}

    def load(self, session: Any, labels: set[str]) -> None:
        for label in labels:
            rows = session.run(
                f"MATCH (n:{label}) RETURN elementId(n) AS eid, properties(n) AS props"
            )
            for row in rows:
                props = dict(row["props"] or {})
                name = props.get("名称") or props.get("name")
                if not name:
                    continue
                self.remember(label, str(name), eid=row["eid"], props=props)

    def remember(
        self, label: str, name: str, *, eid: str | None, props: dict[str, Any]
    ) -> None:
        self.by_label_name[(label, name)] = {"eid": eid, "props": props}
        for alias in _lookup_values(props):
            self.by_label_alias.setdefault((label, alias), name)

    def find(
        self, label: str, names: list[str], *, include_aliases: bool
    ) -> dict[str, Any] | None:
        for name in names:
            hit = self.by_label_name.get((label, name))
            if hit:
                return hit
        if not include_aliases:
            return None
        for name in names:
            canonical = self.by_label_alias.get((label, name))
            if canonical:
                hit = self.by_label_name.get((label, canonical))
                if hit:
                    return hit
        return None


def ensure_name_indexes(session: Any) -> list[str]:
    created: list[str] = []
    for node_type in NodeType:
        label = to_neo4j_label(node_type)
        constraint = f"baicao_{node_type.name}_name"
        try:
            session.run(
                f"CREATE CONSTRAINT {constraint} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.名称 IS UNIQUE"
            )
        except Exception as exc:
            session.run(f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.名称)")
            print(
                f"name uniqueness unavailable for {label}, using index: {exc}",
                file=sys.stderr,
            )
        created.append(label)
    return created


def find_existing(
    tx: Any, label: str, names: list[str], *, include_aliases: bool = True
) -> dict[str, Any] | None:
    result = tx.run(
        f"""
        MATCH (n:{label})
        WHERE n.名称 IN $names
        RETURN elementId(n) AS eid, properties(n) AS props
        LIMIT 5
        """,
        names=names,
    )
    rows = list(result)
    if not rows and include_aliases:
        result = tx.run(
            f"""
            MATCH (n:{label})
            WHERE any(key IN $lookup_keys WHERE properties(n)[key] IN $names)
            RETURN elementId(n) AS eid, properties(n) AS props
            LIMIT 5
            """,
            names=names,
            lookup_keys=list(GRAPH_FIND_KEYS),
        )
        rows = list(result)
    if not rows:
        return None
    exact = next(
        (row for row in rows if (row["props"].get("名称") or row["props"].get("name")) in names),
        rows[0],
    )
    return {"eid": exact["eid"], "props": dict(exact["props"])}


def _update_nodes_query(label: str) -> str:
    return f"""
        UNWIND $rows AS row
        MATCH (n:{label}) WHERE elementId(n) = row.eid
        SET n += row.filled
        SET n.导入源列表 = CASE
          WHEN n.导入源列表 IS NULL THEN [row.source_id]
          WHEN row.source_id IN n.导入源列表 THEN n.导入源列表
          ELSE n.导入源列表 + row.source_id
        END
        SET n.导入批次列表 = CASE
          WHEN n.导入批次列表 IS NULL THEN [row.batch_id]
          WHEN row.batch_id IN n.导入批次列表 THEN n.导入批次列表
          ELSE n.导入批次列表 + row.batch_id
        END
        SET n.导入范围键列表 = CASE
          WHEN n.导入范围键列表 IS NULL THEN [row.scope]
          WHEN row.scope IN n.导入范围键列表 THEN n.导入范围键列表
          ELSE n.导入范围键列表 + row.scope
        END
        SET n.抽取契约哈希列表 = CASE
          WHEN n.抽取契约哈希列表 IS NULL THEN [row.prompt_hash]
          WHEN row.prompt_hash IN n.抽取契约哈希列表 THEN n.抽取契约哈希列表
          ELSE n.抽取契约哈希列表 + row.prompt_hash
        END
        """


def _merge_nodes_query(label: str) -> str:
    return f"""
        UNWIND $rows AS row
        MERGE (n:{label} {{名称: row.name}})
        ON CREATE SET n += row.props, n.标识 = coalesce(n.标识, row.node_id)
        ON MATCH SET n.导入源列表 = CASE
              WHEN n.导入源列表 IS NULL THEN [row.source_id]
              WHEN row.source_id IN n.导入源列表 THEN n.导入源列表
              ELSE n.导入源列表 + row.source_id
            END
        RETURN row.name AS name, elementId(n) AS eid, properties(n) AS props
        """


def _merge_edges_query(source_label: str, rel: str, target_label: str) -> str:
    return f"""
        UNWIND $rows AS row
        MATCH (source:{source_label} {{名称: row.source_name}})
        MATCH (target:{target_label} {{名称: row.target_name}})
        MERGE (source)-[r:{rel} {{导入范围键: row.scope}}]->(target)
        SET r.导入源 = row.source_id
        SET r.导入批次 = row.batch_id
        SET r.导入单元 = row.unit_id
        SET r.抽取契约哈希 = row.prompt_hash
        FOREACH (_ IN CASE WHEN row.dosage IS NULL THEN [] ELSE [1] END |
          SET r.剂量 = row.dosage
        )
        FOREACH (_ IN CASE WHEN row.dosage_ratio IS NULL THEN [] ELSE [1] END |
          SET r.剂量比例 = row.dosage_ratio
        )
        FOREACH (_ IN CASE WHEN row.evidence_ref IS NULL THEN [] ELSE [1] END |
          SET r.证据定位 = row.evidence_ref
        )
        RETURN row.idx AS idx
        """


def write_node(
    tx: Any,
    record: DatasetRecord,
    stats: Counter,
    *,
    include_aliases: bool = True,
    cache: NodeCache | None = None,
) -> str:
    label = to_neo4j_label(record.node_type)
    names = _record_lookup_names(record)
    existing = (
        cache.find(label, names, include_aliases=include_aliases)
        if cache is not None
        else find_existing(tx, label, names, include_aliases=include_aliases)
    )
    meta = _import_meta(record)
    if existing and existing.get("eid"):
        filled = _filled_props(existing["props"], record)
        tx.run(
            _update_nodes_query(label),
            rows=[{"eid": existing["eid"], "filled": filled, **meta}],
        )
        stats["merged"] += 1
        return existing["props"].get("名称") or existing["props"].get("name")
    props = _create_node_props(record)
    tx.run(
        _merge_nodes_query(label),
        rows=[
            {
                "name": record.node_name,
                "props": props,
                "node_id": f"{label}-{record.node_name}",
                **meta,
            }
        ],
    )
    stats["created"] += 1
    return record.node_name


def write_edges(
    tx: Any,
    record: DatasetRecord,
    resolved_name: str,
    stats: Counter,
    *,
    resolved_targets: dict[tuple[str, str], str] | None = None,
    cache: NodeCache | None = None,
    preexisting_labels: set[str] | None = None,
) -> None:
    source_label = to_neo4j_label(record.node_type)
    for edge in record.edges:
        rel = to_neo4j_rel(edge.type)
        target_types = EDGE_TARGET_TYPES.get(edge.type)
        if target_types is None:
            raise ValueError(f"unsupported import edge type: {edge.type}")
        target_names = lookup_names(target_types[0], edge.target)
        target_labels = [to_neo4j_label(target_type) for target_type in target_types]
        resolved = _resolve_edge_target(
            edge,
            cache=cache,
            resolved_targets=resolved_targets,
            preexisting_labels=preexisting_labels or set(),
        )
        resolved_target = resolved[1] if resolved else None
        if resolved:
            match_body = f"""
            MATCH (source:{source_label} {{名称: $source_name}})
            MATCH (target:{resolved[0]})
            WHERE target.名称 = $resolved_target
            """
        elif len(target_labels) == 1:
            match_body = f"""
            MATCH (source:{source_label} {{名称: $source_name}})
            MATCH (target:{target_labels[0]})
            WHERE any(key IN $target_name_keys WHERE properties(target)[key] IN $target_names)
            """
        else:
            union_parts = [
                f"""
                MATCH (source:{source_label} {{名称: $source_name}})
                MATCH (target:{label})
                WHERE any(key IN $target_name_keys WHERE properties(target)[key] IN $target_names)
                RETURN source, target
                """
                for label in target_labels
            ]
            match_body = "CALL { " + " UNION ".join(union_parts) + " }"
        dosage = (edge.properties or {}).get("dosage")
        dosage_ratio = (edge.properties or {}).get("dosage_ratio")
        evidence_ref = (edge.properties or {}).get("evidence_ref")
        localized = to_graph_properties(
            {
                "import_source_id": record.source_id,
                "import_batch_id": record.batch_id,
                "import_unit_id": record.unit_id,
                "import_scope_key": record.import_scope_key,
                "prompt_hash": record.prompt_hash,
                "dosage": dosage,
                "dosage_ratio": dosage_ratio,
                "evidence_ref": evidence_ref,
            }
        )
        result = tx.run(
            f"""
            {match_body}
            WITH source, target LIMIT 1
            MERGE (source)-[r:{rel} {{导入范围键: $scope}}]->(target)
            SET r.导入源 = $source_id
            SET r.导入批次 = $batch_id
            SET r.导入单元 = $unit_id
            SET r.抽取契约哈希 = $prompt_hash
            FOREACH (_ IN CASE WHEN $dosage IS NULL THEN [] ELSE [1] END |
              SET r.剂量 = $dosage
            )
            FOREACH (_ IN CASE WHEN $dosage_ratio IS NULL THEN [] ELSE [1] END |
              SET r.剂量比例 = $dosage_ratio
            )
            FOREACH (_ IN CASE WHEN $evidence_ref IS NULL THEN [] ELSE [1] END |
              SET r.证据定位 = $evidence_ref
            )
            RETURN type(r) AS rel
            """,
            source_name=resolved_name,
            target_names=target_names,
            target_name_keys=["名称", *GRAPH_FIND_KEYS],
            target_labels=target_labels,
            resolved_target=resolved_target,
            scope=localized.get("导入范围键"),
            source_id=localized.get("导入源"),
            batch_id=record.batch_id,
            unit_id=record.unit_id,
            prompt_hash=record.prompt_hash,
            dosage=dosage,
            dosage_ratio=localized.get("剂量比例"),
            evidence_ref=localized.get("证据定位"),
        )
        if result.single() is None:
            stats["dangling_edges"] += 1
        else:
            stats["edges"] += 1


def _resolve_edge_target(
    edge: DatasetEdge,
    *,
    cache: NodeCache | None,
    resolved_targets: dict[tuple[str, str], str] | None,
    preexisting_labels: set[str],
) -> tuple[str, str] | None:
    target_types = EDGE_TARGET_TYPES.get(edge.type)
    if target_types is None:
        raise ValueError(f"unsupported import edge type: {edge.type}")
    for target_type in target_types:
        if resolved_targets and (target_type, edge.target) in resolved_targets:
            return to_neo4j_label(target_type), resolved_targets[(target_type, edge.target)]
    if cache is None:
        return None
    for target_type in target_types:
        label = to_neo4j_label(target_type)
        names = lookup_names(target_type, edge.target)
        hit = cache.find(
            label, names, include_aliases=label in preexisting_labels
        )
        if hit:
            name = hit["props"].get("名称") or hit["props"].get("name")
            if name:
                return label, str(name)
    return None


@dataclass
class NodeWritePlan:
    resolved: list[tuple[DatasetRecord, str]] = field(default_factory=list)
    updates: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    creates: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    stats: Counter = field(default_factory=Counter)


def plan_node_writes(
    records: tuple[DatasetRecord, ...] | list[DatasetRecord],
    cache: NodeCache,
    preexisting_labels: set[str],
) -> NodeWritePlan:
    plan = NodeWritePlan()
    pending: dict[tuple[str, str], dict[str, Any]] = {}
    pending_alias: dict[tuple[str, str], str] = {}
    for record in records:
        label = to_neo4j_label(record.node_type)
        names = _record_lookup_names(record)
        include_aliases = label in preexisting_labels
        existing = cache.find(label, names, include_aliases=include_aliases)
        if existing is None:
            for name in names:
                canonical = pending.get((label, name))
                if canonical is None and include_aliases:
                    mapped = pending_alias.get((label, name))
                    canonical = pending.get((label, mapped)) if mapped else None
                if canonical is not None:
                    existing = {"eid": None, "props": canonical["props"], "pending": canonical}
                    break
        meta = _import_meta(record)
        if existing and existing.get("eid"):
            filled = _filled_props(existing["props"], record)
            name = existing["props"].get("名称") or existing["props"].get("name")
            plan.updates[label].append(
                {"eid": existing["eid"], "name": name, "filled": filled, **meta}
            )
            plan.stats["merged"] += 1
            plan.resolved.append((record, str(name)))
            continue
        if existing and existing.get("pending") is not None:
            pending_row = existing["pending"]
            props = pending_row["props"]
            for key, value in _filled_props(props, record).items():
                if props.get(key) in (None, "", [], {}):
                    props[key] = value
            _append_prop_list(props, "导入源列表", meta["source_id"])
            _append_prop_list(props, "导入批次列表", meta["batch_id"])
            _append_prop_list(props, "导入范围键列表", meta["scope"])
            _append_prop_list(props, "抽取契约哈希列表", meta["prompt_hash"])
            plan.stats["merged"] += 1
            plan.resolved.append((record, pending_row["name"]))
            continue
        props = _create_node_props(record)
        row = {
            "name": record.node_name,
            "props": props,
            "node_id": f"{label}-{record.node_name}",
            **meta,
        }
        plan.creates[label].append(row)
        pending[(label, record.node_name)] = row
        if include_aliases:
            for name in names:
                pending_alias.setdefault((label, name), record.node_name)
        plan.stats["created"] += 1
        plan.resolved.append((record, record.node_name))
    return plan


def _run_node_unwinds(
    tx: Any, plan: NodeWritePlan, *, batch_size: int
) -> list[tuple[str, str, str | None, dict[str, Any]]]:
    remember: list[tuple[str, str, str | None, dict[str, Any]]] = []
    for label, rows in plan.updates.items():
        for chunk in batched(rows, _unwind_size(label, batch_size)):
            tx.run(_update_nodes_query(label), rows=list(chunk))
            for row in chunk:
                remember.append((label, str(row["name"]), row["eid"], dict(row["filled"])))
    for label, rows in plan.creates.items():
        for chunk in batched(rows, _unwind_size(label, batch_size)):
            chunk_rows = list(chunk)
            result = tx.run(_merge_nodes_query(label), rows=chunk_rows)
            returned = {row["name"]: row for row in result}
            for row in chunk_rows:
                hit = returned.get(row["name"])
                eid = hit["eid"] if hit else None
                props = dict(hit["props"]) if hit else dict(row["props"])
                remember.append((label, row["name"], eid, props))
    return remember


def _write_node_batch(
    tx: Any,
    records: tuple[DatasetRecord, ...],
    preexisting_labels: set[str],
    cache: NodeCache | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> tuple[list[tuple[DatasetRecord, str]], Counter, list[tuple[str, str, str | None, dict[str, Any]]]]:
    plan = plan_node_writes(records, cache or NodeCache(), preexisting_labels)
    remember = _run_node_unwinds(tx, plan, batch_size=batch_size)
    return plan.resolved, plan.stats, remember


def plan_edge_writes(
    items: tuple[tuple[DatasetRecord, str, DatasetEdge], ...] | list[tuple[DatasetRecord, str, DatasetEdge]],
    resolved_targets: dict[tuple[str, str], str],
    cache: NodeCache,
    preexisting_labels: set[str],
) -> tuple[dict[tuple[str, str, str], list[dict[str, Any]]], int]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    dangling = 0
    for index, (record, source_name, edge) in enumerate(items):
        resolved = _resolve_edge_target(
            edge,
            cache=cache,
            resolved_targets=resolved_targets,
            preexisting_labels=preexisting_labels,
        )
        if resolved is None:
            dangling += 1
            continue
        target_label, target_name = resolved
        dosage = (edge.properties or {}).get("dosage")
        dosage_ratio = (edge.properties or {}).get("dosage_ratio")
        evidence_ref = (edge.properties or {}).get("evidence_ref")
        localized = to_graph_properties(
            {
                "import_source_id": record.source_id,
                "import_batch_id": record.batch_id,
                "import_unit_id": record.unit_id,
                "import_scope_key": record.import_scope_key,
                "prompt_hash": record.prompt_hash,
                "dosage": dosage,
                "dosage_ratio": dosage_ratio,
                "evidence_ref": evidence_ref,
            }
        )
        grouped[(to_neo4j_label(record.node_type), to_neo4j_rel(edge.type), target_label)].append(
            {
                "idx": index,
                "source_name": source_name,
                "target_name": target_name,
                "scope": localized.get("导入范围键"),
                "source_id": localized.get("导入源"),
                "batch_id": record.batch_id,
                "unit_id": record.unit_id,
                "prompt_hash": record.prompt_hash,
                "dosage": dosage,
                "dosage_ratio": localized.get("剂量比例"),
                "evidence_ref": localized.get("证据定位"),
            }
        )
    return grouped, dangling


def _run_edge_unwinds(
    tx: Any,
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]],
    dangling: int,
    *,
    batch_size: int,
) -> Counter:
    stats: Counter = Counter(dangling_edges=dangling)
    for (source_label, rel, target_label), rows in grouped.items():
        written = 0
        for chunk in batched(rows, batch_size):
            chunk_rows = list(chunk)
            result = tx.run(
                _merge_edges_query(source_label, rel, target_label),
                rows=chunk_rows,
            )
            written += sum(1 for _ in result)
        missing = len(rows) - written
        stats["edges"] += written
        if missing:
            stats["dangling_edges"] += missing
    return stats


def _write_edge_batch(
    tx: Any,
    resolved: tuple[tuple[DatasetRecord, str] | tuple[DatasetRecord, str, DatasetEdge], ...],
    resolved_targets: dict[tuple[str, str], str],
    cache: NodeCache | None = None,
    preexisting_labels: set[str] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> Counter:
    items: list[tuple[DatasetRecord, str, DatasetEdge]] = []
    for item in resolved:
        if len(item) == 3:
            record, name, edge = item
            items.append((record, name, edge))
        else:
            record, name = item
            items.extend((record, name, edge) for edge in record.edges)
    grouped, dangling = plan_edge_writes(
        items,
        resolved_targets,
        cache or NodeCache(),
        preexisting_labels or set(),
    )
    return _run_edge_unwinds(tx, grouped, dangling, batch_size=batch_size)


def _labels_needed(records: list[DatasetRecord]) -> set[str]:
    labels = {to_neo4j_label(record.node_type) for record in records}
    for record in records:
        for edge in record.edges:
            target_types = EDGE_TARGET_TYPES.get(edge.type)
            if target_types is None:
                raise ValueError(f"unsupported import edge type: {edge.type}")
            labels.update(to_neo4j_label(target_type) for target_type in target_types)
    return labels


def _preexisting_labels(session: Any, records: list[DatasetRecord]) -> set[str]:
    return {
        label
        for label in _labels_needed(records)
        if session.run(f"MATCH (n:{label}) RETURN count(n) > 0 AS present").single()[
            "present"
        ]
    }


def import_records(
    records: list[DatasetRecord],
    driver: Any,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    include_source_graph: bool = False,
) -> dict[str, int]:
    batch_size = clamp_batch_size(batch_size)
    graph_records, payload_stats = graph_store_records(
        records, include_source_graph=include_source_graph
    )
    stats: Counter = Counter(
        skipped_records=int(payload_stats.get("omitted_records", 0)),
        dropped_source_edges=int(payload_stats.get("source_edges", 0)),
        collapsed_records=int(payload_stats.get("collapsed_records", 0)),
    )
    resolved: list[tuple[DatasetRecord, str]] = []
    with driver.session(database="neo4j") as session:
        preexisting_labels = _preexisting_labels(session, graph_records)
        cache = NodeCache()
        cache.load(session, _labels_needed(graph_records))
        for batch in batched(graph_records, batch_size):
            batch_resolved, batch_stats, remember = session.execute_write(
                _write_node_batch, batch, preexisting_labels, cache, batch_size
            )
            for label, name, eid, props in remember:
                if not eid:
                    continue
                previous = cache.by_label_name.get((label, name), {})
                cache.remember(
                    label,
                    name,
                    eid=eid,
                    props={**previous.get("props", {}), **props},
                )
            resolved.extend(batch_resolved)
            stats.update(batch_stats)
        resolved_targets = {
            (record.node_type, record.node_name): name for record, name in resolved
        }
        flat_edges = [
            (record, name, edge)
            for record, name in resolved
            for edge in record.edges
        ]
        for batch in batched(flat_edges, batch_size):
            stats.update(
                session.execute_write(
                    _write_edge_batch,
                    batch,
                    resolved_targets,
                    cache,
                    preexisting_labels,
                    batch_size,
                )
            )
    return dict(stats)


def main() -> None:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=False)
    source.add_argument("--records", type=Path)
    source.add_argument("--dataset-root", type=Path)
    parser.add_argument("--edges", type=Path)
    parser.add_argument("--tier", choices=("public", "restricted", "all"), default="all")
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:17687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "neo4j_password"))
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"UNWIND rows per statement (default {DEFAULT_BATCH_SIZE}, max {MAX_BATCH_SIZE})",
    )
    parser.add_argument(
        "--include-source-graph",
        action="store_true",
        help="write 来源于 edges, 来源 nodes, and evidence_text onto Neo4j",
    )
    parser.add_argument(
        "--mode",
        choices=("admin", "bolt", "indexes"),
        default="admin",
        help="admin: 默认，折叠 CSV 供 neo4j-admin。indexes: 只给运行中的库建名称索引。bolt: 仅增量 UNWIND",
    )
    parser.add_argument("--admin-dir", type=Path, default=Path("tmp/neo4j-admin-import"))
    args = parser.parse_args()
    if args.mode == "indexes":
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
        driver.verify_connectivity()
        try:
            with driver.session(database="neo4j") as session:
                labels = ensure_name_indexes(session)
        finally:
            driver.close()
        print(json.dumps({"ok": True, "mode": "indexes", "labels": labels}, ensure_ascii=False))
        return
    if args.records is None and args.dataset_root is None:
        raise SystemExit("need --records or --dataset-root")
    try:
        batch_size = clamp_batch_size(args.batch_size)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    records = load_import_records(
        records_path=args.records,
        edges_path=args.edges,
        dataset_root=args.dataset_root,
        tier=args.tier,
    )
    if not records:
        raise SystemExit("no records in import source")
    stamped = prepare_import_records(records, prompt_file=args.prompt_file)
    _, payload_stats = graph_store_records(
        stamped, include_source_graph=args.include_source_graph
    )
    if args.dry_run or args.mode == "admin":
        payload = {
            "dry_run": args.dry_run or args.mode == "admin",
            "mode": args.mode,
            "records": len(stamped),
            "graph_records": payload_stats.get("graph_records", 0),
            "omitted_records": payload_stats.get("omitted_records", 0),
            "source_edges_in_dataset": payload_stats.get("source_edges", 0),
            "graph_edges": payload_stats.get("graph_edges", 0),
            "include_source_graph": args.include_source_graph,
            "sources": sorted({record.source_id for record in stamped}),
            "batch_size": batch_size,
        }
        if args.mode == "admin" and not args.dry_run:
            payload.update(
                write_admin_csvs(
                    stamped,
                    args.admin_dir,
                    include_source_graph=args.include_source_graph,
                )
            )
            payload["dry_run"] = False
            payload["admin_script"] = str(args.admin_dir / "neo4j-admin.sh")
        print(json.dumps(payload, ensure_ascii=False))
        return
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    driver.verify_connectivity()
    try:
        with driver.session(database="neo4j") as session:
            ensure_name_indexes(session)
        stats = import_records(
            stamped,
            driver,
            batch_size=batch_size,
            include_source_graph=args.include_source_graph,
        )
    finally:
        driver.close()
    print(json.dumps({"ok": True, **stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
