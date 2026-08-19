"""把数据集 latest 按同名/别名启发式合并写入 Neo4j。已有节点只补空属性，不覆盖药典字段。"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from itertools import batched
from pathlib import Path
from typing import Any

from knowledge_model.constants import to_neo4j_label, to_neo4j_rel
from knowledge_model.graph_i18n import to_graph_properties

from data_ingestion.dataset_records import DatasetRecord
from data_ingestion.provenance import (
    append_unique,
    fill_if_empty,
    graph_node_props,
    is_skip_record,
    lookup_names,
    prompt_hash_for,
    scope_key_for,
    slim_record,
    DEFAULT_PROMPT_FILES,
)


def load_jsonl(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = DatasetRecord.model_validate(json.loads(line))
            record.validate_types()
            records.append(record)
    return records


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
            lookup_keys=[
                "name",
                "别名",
                "alias",
                "拼音",
                "pinyin_name",
                "拉丁名",
                "latin_name",
            ],
        )
        rows = list(result)
    if not rows:
        return None
    exact = next(
        (row for row in rows if (row["props"].get("名称") or row["props"].get("name")) in names),
        rows[0],
    )
    return {"eid": exact["eid"], "props": dict(exact["props"])}


def write_node(
    tx: Any,
    record: DatasetRecord,
    stats: Counter,
    *,
    include_aliases: bool = True,
) -> str:
    label = to_neo4j_label(record.node_type)
    names = lookup_names(record.node_type, record.node_name)
    if alias := (record.properties or {}).get("alias"):
        names = append_unique(names, str(alias))
    existing = find_existing(tx, label, names, include_aliases=include_aliases)
    if existing:
        existing_en = {
            **existing["props"],
            **{
                en: existing["props"][zh]
                for zh, en in {
                    "名称": "name",
                    "拉丁名": "latin_name",
                    "拼音": "pinyin_name",
                }.items()
                if zh in existing["props"]
            },
        }
        filled = to_graph_properties(fill_if_empty(existing_en, graph_node_props(record)))
        tx.run(
            f"""
            MATCH (n:{label}) WHERE elementId(n) = $eid
            SET n += $filled
            SET n.导入源列表 = CASE
              WHEN n.导入源列表 IS NULL THEN [$source_id]
              WHEN $source_id IN n.导入源列表 THEN n.导入源列表
              ELSE n.导入源列表 + $source_id
            END
            SET n.导入批次列表 = CASE
              WHEN n.导入批次列表 IS NULL THEN [$batch_id]
              WHEN $batch_id IN n.导入批次列表 THEN n.导入批次列表
              ELSE n.导入批次列表 + $batch_id
            END
            SET n.导入范围键列表 = CASE
              WHEN n.导入范围键列表 IS NULL THEN [$scope]
              WHEN $scope IN n.导入范围键列表 THEN n.导入范围键列表
              ELSE n.导入范围键列表 + $scope
            END
            SET n.抽取契约哈希列表 = CASE
              WHEN n.抽取契约哈希列表 IS NULL THEN [$prompt_hash]
              WHEN $prompt_hash IN n.抽取契约哈希列表 THEN n.抽取契约哈希列表
              ELSE n.抽取契约哈希列表 + $prompt_hash
            END
            """,
            eid=existing["eid"],
            filled=filled,
            source_id=to_graph_properties({"import_source_id": record.source_id})["导入源"],
            batch_id=record.batch_id,
            scope=to_graph_properties({"import_scope_key": record.import_scope_key or ""})["导入范围键"],
            prompt_hash=record.prompt_hash,
        )
        stats["merged"] += 1
        return existing["props"].get("名称") or existing["props"].get("name")
    props = to_graph_properties(
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
    tx.run(
        f"""
        MERGE (n:{label} {{名称: $name}})
        ON CREATE SET n += $props, n.标识 = coalesce(n.标识, $node_id)
        ON MATCH SET n.导入源列表 = CASE
              WHEN n.导入源列表 IS NULL THEN [$source_id]
              WHEN $source_id IN n.导入源列表 THEN n.导入源列表
              ELSE n.导入源列表 + $source_id
            END
        """,
        name=record.node_name,
        props=props,
        node_id=f"{label}-{record.node_name}",
        source_id=props.get("导入源"),
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
) -> None:
    source_label = to_neo4j_label(record.node_type)
    for edge in record.edges:
        rel = to_neo4j_rel(edge.type)
        target_types = {
            "组成药材": ("药材", "饮片"),
            "使用方剂": ("方剂",),
            "取用穴位": ("穴位",),
            "采用治法": ("治法",),
            "治疗病证": ("病证",),
            "关联药材": ("药材",),
            "关联治法": ("治法",),
            "关联证候": ("病证",),
            "记载于医案": ("医案",),
            "由证据支持": ("证据",),
            "来源于": ("来源",),
            "经过工艺": ("工艺",),
            "具有功效": ("功效",),
            "具有性味": ("性味",),
            "归于经脉": ("归经",),
            "具有饮片": ("饮片",),
        }.get(edge.type)
        if target_types is None:
            raise ValueError(f"unsupported import edge type: {edge.type}")
        target_names = lookup_names(target_types[0], edge.target)
        target_labels = [to_neo4j_label(target_type) for target_type in target_types]
        resolved_target = next(
            (
                resolved_targets[(target_type, edge.target)]
                for target_type in target_types
                if resolved_targets and (target_type, edge.target) in resolved_targets
            ),
            None,
        )
        target_match = (
            f"MATCH (target:{target_labels[0]})"
            if len(target_labels) == 1
            else "MATCH (target)"
        )
        target_where = (
            "target.名称 = $resolved_target"
            if resolved_target
            else "any(key IN $target_name_keys WHERE properties(target)[key] IN $target_names)"
        )
        if len(target_labels) > 1:
            target_where = (
                "any(target_label IN labels(target) WHERE target_label IN $target_labels) "
                f"AND {target_where}"
            )
        dosage = (edge.properties or {}).get("dosage")
        localized = to_graph_properties(
            {
                "import_source_id": record.source_id,
                "import_batch_id": record.batch_id,
                "import_unit_id": record.unit_id,
                "import_scope_key": record.import_scope_key,
                "prompt_hash": record.prompt_hash,
                "dosage": dosage,
            }
        )
        result = tx.run(
            f"""
            MATCH (source:{source_label} {{名称: $source_name}})
            {target_match}
            WHERE {target_where}
            WITH source, target LIMIT 1
            MERGE (source)-[r:{rel} {{导入范围键: $scope}}]->(target)
            SET r.导入源 = $source_id
            SET r.导入批次 = $batch_id
            SET r.导入单元 = $unit_id
            SET r.抽取契约哈希 = $prompt_hash
            FOREACH (_ IN CASE WHEN $dosage IS NULL THEN [] ELSE [1] END |
              SET r.剂量 = $dosage
            )
            RETURN type(r) AS rel
            """,
            source_name=resolved_name,
            target_names=target_names,
            target_name_keys=["名称", "name", "别名", "alias"],
            target_labels=target_labels,
            resolved_target=resolved_target,
            scope=localized.get("导入范围键"),
            source_id=localized.get("导入源"),
            batch_id=record.batch_id,
            unit_id=record.unit_id,
            prompt_hash=record.prompt_hash,
            dosage=dosage,
        )
        if result.single() is None:
            stats["dangling_edges"] += 1
        else:
            stats["edges"] += 1


def _write_node_batch(
    tx: Any,
    records: tuple[DatasetRecord, ...],
    preexisting_labels: set[str],
) -> tuple[list[tuple[DatasetRecord, str]], Counter]:
    stats: Counter = Counter()
    resolved = [
        (
            record,
            write_node(
                tx,
                record,
                stats,
                include_aliases=to_neo4j_label(record.node_type) in preexisting_labels,
            ),
        )
        for record in records
    ]
    return resolved, stats


def _write_edge_batch(
    tx: Any,
    resolved: tuple[tuple[DatasetRecord, str], ...],
    resolved_targets: dict[tuple[str, str], str],
) -> Counter:
    stats: Counter = Counter()
    for record, name in resolved:
        write_edges(tx, record, name, stats, resolved_targets=resolved_targets)
    return stats


def _preexisting_labels(session: Any, records: list[DatasetRecord]) -> set[str]:
    labels = {to_neo4j_label(record.node_type) for record in records}
    return {
        label
        for label in labels
        if session.run(f"MATCH (n:{label}) RETURN count(n) > 0 AS present").single()[
            "present"
        ]
    }


def import_records(
    records: list[DatasetRecord], driver: Any, *, batch_size: int = 100
) -> dict[str, int]:
    stats: Counter = Counter()
    graph_records = [record for record in records if not is_skip_record(record)]
    stats["skipped_records"] = len(records) - len(graph_records)
    resolved: list[tuple[DatasetRecord, str]] = []
    with driver.session(database="neo4j") as session:
        preexisting_labels = _preexisting_labels(session, graph_records)
        for batch in batched(graph_records, batch_size):
            batch_resolved, batch_stats = session.execute_write(
                _write_node_batch, batch, preexisting_labels
            )
            resolved.extend(batch_resolved)
            stats.update(batch_stats)
        resolved_targets = {
            (record.node_type, record.node_name): name for record, name in resolved
        }
        edge_records = [item for item in resolved if item[0].edges]
        for batch in batched(edge_records, batch_size):
            stats.update(
                session.execute_write(_write_edge_batch, batch, resolved_targets)
            )
    return dict(stats)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:17687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "neo4j_password"))
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    records = load_jsonl(args.records)
    if not records:
        raise SystemExit(f"no records in {args.records}")
    source_id = records[0].source_id
    prompt_file = args.prompt_file or DEFAULT_PROMPT_FILES.get(source_id)
    prompt_hash = records[0].prompt_hash
    if not prompt_hash:
        if prompt_file is None or not prompt_file.is_file():
            raise SystemExit("records missing prompt_hash; pass --prompt-file")
        prompt_hash = prompt_hash_for(prompt_file)
    scope = records[0].import_scope_key or scope_key_for(source_id)
    stamped = [slim_record(record, prompt_hash=prompt_hash, import_scope_key=scope) for record in records]
    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "records": len(stamped),
                    "graph_records": sum(1 for record in stamped if not is_skip_record(record)),
                    "prompt_hash": prompt_hash,
                    "import_scope_key": scope,
                },
                ensure_ascii=False,
            )
        )
        return
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    driver.verify_connectivity()
    try:
        stats = import_records(stamped, driver)
    finally:
        driver.close()
    print(json.dumps({"ok": True, "prompt_hash": prompt_hash, **stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
