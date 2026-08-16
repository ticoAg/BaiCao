"""把数据集 latest 按同名/别名启发式合并写入 Neo4j。已有节点只补空属性，不覆盖药典字段。"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from knowledge_model.constants import to_neo4j_label, to_neo4j_rel

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


def find_existing(tx: Any, label: str, names: list[str]) -> dict[str, Any] | None:
    result = tx.run(
        f"""
        MATCH (n:{label})
        WHERE n.name IN $names
           OR n.alias IN $names
           OR n.pinyin_name IN $names
           OR n.latin_name IN $names
           OR (n.aliases IS NOT NULL AND any(a IN n.aliases WHERE a IN $names))
        RETURN elementId(n) AS eid, properties(n) AS props
        LIMIT 5
        """,
        names=names,
    )
    rows = list(result)
    if not rows:
        return None
    exact = next((row for row in rows if row["props"].get("name") in names), rows[0])
    return {"eid": exact["eid"], "props": dict(exact["props"])}


def write_node(tx: Any, record: DatasetRecord, stats: Counter) -> str:
    label = to_neo4j_label(record.node_type)
    names = lookup_names(record.node_type, record.node_name)
    if alias := (record.properties or {}).get("alias"):
        names = append_unique(names, str(alias))
    existing = find_existing(tx, label, names)
    incoming = graph_node_props(record)
    if existing:
        filled = fill_if_empty(existing["props"], incoming)
        tx.run(
            f"""
            MATCH (n:{label}) WHERE elementId(n) = $eid
            SET n += $filled
            SET n.import_source_ids = CASE
              WHEN n.import_source_ids IS NULL THEN [$source_id]
              WHEN $source_id IN n.import_source_ids THEN n.import_source_ids
              ELSE n.import_source_ids + $source_id
            END
            SET n.import_batch_ids = CASE
              WHEN n.import_batch_ids IS NULL THEN [$batch_id]
              WHEN $batch_id IN n.import_batch_ids THEN n.import_batch_ids
              ELSE n.import_batch_ids + $batch_id
            END
            SET n.import_scope_keys = CASE
              WHEN n.import_scope_keys IS NULL THEN [$scope]
              WHEN $scope IN n.import_scope_keys THEN n.import_scope_keys
              ELSE n.import_scope_keys + $scope
            END
            SET n.prompt_hashes = CASE
              WHEN n.prompt_hashes IS NULL THEN [$prompt_hash]
              WHEN $prompt_hash IN n.prompt_hashes THEN n.prompt_hashes
              ELSE n.prompt_hashes + $prompt_hash
            END
            """,
            eid=existing["eid"],
            filled=filled,
            source_id=record.source_id,
            batch_id=record.batch_id,
            scope=record.import_scope_key,
            prompt_hash=record.prompt_hash,
        )
        stats["merged"] += 1
        return existing["props"]["name"]
    props = {
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
        **incoming,
    }
    if record.node_type in {"医案", "证据"}:
        props["import_unit_id"] = record.unit_id
    tx.run(
        f"""
        MERGE (n:{label} {{name: $name}})
        ON CREATE SET n += $props, n.id = coalesce(n.id, $node_id)
        ON MATCH SET n.import_source_ids = CASE
              WHEN n.import_source_ids IS NULL THEN [$source_id]
              WHEN $source_id IN n.import_source_ids THEN n.import_source_ids
              ELSE n.import_source_ids + $source_id
            END
        """,
        name=record.node_name,
        props=props,
        node_id=f"{label.lower()}-{record.node_name}",
        source_id=record.source_id,
    )
    stats["created"] += 1
    return record.node_name


def write_edges(tx: Any, record: DatasetRecord, resolved_name: str, stats: Counter) -> None:
    source_label = to_neo4j_label(record.node_type)
    for edge in record.edges:
        rel = to_neo4j_rel(edge.type)
        target_type = {
            "组成药材": "药材",
            "使用方剂": "方剂",
            "取用穴位": "穴位",
            "采用治法": "治法",
            "治疗病证": "病证",
            "记载于医案": "医案",
            "由证据支持": "证据",
            "来源于": "来源",
            "经过工艺": "工艺",
            "具有功效": "功效",
            "具有性味": "性味",
            "归于经脉": "归经",
            "具有饮片": "饮片",
        }.get(edge.type, "")
        target_names = lookup_names(target_type, edge.target)
        dosage = (edge.properties or {}).get("dosage")
        result = tx.run(
            f"""
            MATCH (source:{source_label} {{name: $source_name}})
            MATCH (target)
            WHERE target.name IN $target_names
               OR target.alias IN $target_names
               OR (target.aliases IS NOT NULL AND any(a IN target.aliases WHERE a IN $target_names))
            WITH source, target LIMIT 1
            MERGE (source)-[r:{rel} {{import_scope_key: $scope}}]->(target)
            SET r.import_source_id = $source_id
            SET r.import_batch_id = $batch_id
            SET r.import_unit_id = $unit_id
            SET r.prompt_hash = $prompt_hash
            FOREACH (_ IN CASE WHEN $dosage IS NULL THEN [] ELSE [1] END |
              SET r.dosage = $dosage
            )
            RETURN type(r) AS rel
            """,
            source_name=resolved_name,
            target_names=target_names,
            scope=record.import_scope_key,
            source_id=record.source_id,
            batch_id=record.batch_id,
            unit_id=record.unit_id,
            prompt_hash=record.prompt_hash,
            dosage=dosage,
        )
        if result.single() is None:
            stats["dangling_edges"] += 1
        else:
            stats["edges"] += 1


def import_records(records: list[DatasetRecord], driver: Any) -> dict[str, int]:
    stats: Counter = Counter()
    graph_records = [record for record in records if not is_skip_record(record)]
    stats["skipped_records"] = len(records) - len(graph_records)
    resolved: list[tuple[DatasetRecord, str]] = []
    with driver.session(database="neo4j") as session:
        for record in graph_records:
            name = session.execute_write(write_node, record, stats)
            resolved.append((record, name))
        for record, name in resolved:
            session.execute_write(write_edges, record, name, stats)
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
