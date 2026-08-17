"""合并图上近重复文本：属性值改写 + 共享词条节点合并。不合语义近义。"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from typing import Any

from knowledge_model.text_normalize import (
    SHARED_MERGE_LABELS,
    canonicalize_name,
    name_surface_key,
    pick_canonical,
    property_kind,
    surface_key,
)

TEXT_PROPERTY_KEYS = ("贮藏", "用法", "注意", "炮制方法", "出处书名", "主治", "说明")
LIST_PROPS = ("导入源列表", "导入批次列表", "导入范围键列表", "抽取契约哈希列表", "主治")


def _jsonable(value: object) -> object:
    if hasattr(value, "iso_format"):
        return value.iso_format()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def plan_property_rewrites(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        kind = property_kind(row["key"])
        if kind is None:
            continue
        grouped[(row["key"], kind)].append(row)
    actions: list[dict[str, Any]] = []
    for (key, kind), items in grouped.items():
        if kind == "term":
            values: list[str] = []
            for item in items:
                raw = item["value"]
                if isinstance(raw, list):
                    values.extend(str(part) for part in raw if part)
                elif raw:
                    values.append(str(raw))
            canonical_by_surface = {}
            buckets: dict[str, list[str]] = defaultdict(list)
            for value in values:
                buckets[surface_key(value)].append(value)
            for surface, variants in buckets.items():
                if not surface:
                    continue
                canonical_by_surface[surface] = pick_canonical(variants, kind="term")
            for item in items:
                raw = item["value"]
                if isinstance(raw, list):
                    rewritten = [canonical_by_surface.get(surface_key(str(part)), str(part)) for part in raw]
                    rewritten = list(dict.fromkeys(rewritten))
                    if rewritten != list(raw):
                        actions.append(
                            {
                                "kind": "property",
                                "eid": item["eid"],
                                "key": key,
                                "from": raw,
                                "to": rewritten,
                            }
                        )
                elif raw:
                    canonical = canonical_by_surface.get(surface_key(str(raw)))
                    if canonical and canonical != raw:
                        actions.append(
                            {
                                "kind": "property",
                                "eid": item["eid"],
                                "key": key,
                                "from": raw,
                                "to": canonical,
                            }
                        )
            continue
        buckets = defaultdict(list)
        for item in items:
            if item["value"]:
                buckets[surface_key(str(item["value"]))].append(item)
        for surface, group in buckets.items():
            if not surface:
                continue
            canonical = pick_canonical((str(item["value"]) for item in group), kind=kind)
            for item in group:
                if str(item["value"]) != canonical:
                    actions.append(
                        {
                            "kind": "property",
                            "eid": item["eid"],
                            "key": key,
                            "from": item["value"],
                            "to": canonical,
                        }
                    )
    return actions


def plan_node_merges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        label = node["label"]
        if label not in SHARED_MERGE_LABELS:
            continue
        buckets[(label, name_surface_key(node["name"], label))].append(node)
    actions: list[dict[str, Any]] = []
    for (label, surface), group in buckets.items():
        if not surface:
            continue
        weighted: list[str] = []
        for node in group:
            mapped = canonicalize_name(node["name"], label)
            weighted.extend([mapped] * max(int(node.get("degree") or 1), 1))
        canonical = pick_canonical(weighted, kind="term")
        if label == "性味":
            canonical = canonicalize_name(canonical, label)
        survivor = max(group, key=lambda node: (node.get("degree", 0), len(node.get("props") or {}), node["name"] == canonical))
        drop = [node for node in group if node["eid"] != survivor["eid"]]
        if drop or survivor["name"] != canonical:
            actions.append(
                {
                    "kind": "node",
                    "label": label,
                    "surface": surface,
                    "keep": survivor["eid"],
                    "keep_name": survivor["name"],
                    "canonical": canonical,
                    "drop": [{"eid": node["eid"], "name": node["name"]} for node in drop],
                }
            )
    return actions


def load_property_rows(session: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in TEXT_PROPERTY_KEYS:
        result = session.run(
            f"MATCH (n) WHERE n.`{key}` IS NOT NULL RETURN elementId(n) AS eid, n.`{key}` AS value"
        )
        for record in result:
            rows.append({"eid": record["eid"], "key": key, "value": _jsonable(record["value"])})
    return rows


def load_shared_nodes(session: Any) -> list[dict[str, Any]]:
    result = session.run(
        """
        MATCH (n)
        WHERE any(label IN labels(n) WHERE label IN $labels) AND n.名称 IS NOT NULL
        OPTIONAL MATCH (n)-[r]-()
        RETURN elementId(n) AS eid, labels(n)[0] AS label, n.名称 AS name,
               properties(n) AS props, count(r) AS degree
        """,
        labels=list(SHARED_MERGE_LABELS),
    )
    return [
        {
            "eid": record["eid"],
            "label": record["label"],
            "name": record["name"],
            "props": dict(record["props"] or {}),
            "degree": record["degree"],
        }
        for record in result
    ]


def apply_property_actions(session: Any, actions: list[dict[str, Any]]) -> int:
    changed = 0
    for action in actions:
        if action["kind"] != "property":
            continue
        session.run(
            f"MATCH (n) WHERE elementId(n) = $eid SET n.`{action['key']}` = $value",
            eid=action["eid"],
            value=action["to"],
        )
        changed += 1
    return changed


def _union_lists(keep: dict[str, Any], drop: dict[str, Any]) -> dict[str, Any]:
    merged = dict(keep)
    for key, value in drop.items():
        if key not in merged or merged[key] in (None, "", [], {}):
            merged[key] = value
            continue
        if key in LIST_PROPS and isinstance(merged[key], list) and isinstance(value, list):
            merged[key] = list(dict.fromkeys([*merged[key], *value]))
    return merged


def apply_node_actions(session: Any, actions: list[dict[str, Any]]) -> dict[str, int]:
    merged = 0
    renamed = 0
    for action in actions:
        if action["kind"] != "node":
            continue
        for drop in action["drop"]:
            keep_props = session.run(
                "MATCH (n) WHERE elementId(n) = $eid RETURN properties(n) AS props",
                eid=action["keep"],
            ).single()
            drop_row = session.run(
                "MATCH (n) WHERE elementId(n) = $eid RETURN properties(n) AS props",
                eid=drop["eid"],
            ).single()
            if keep_props is None or drop_row is None:
                continue
            combined = _union_lists(dict(keep_props["props"]), dict(drop_row["props"]))
            combined["名称"] = action["canonical"]
            session.run(
                """
                MATCH (keep) WHERE elementId(keep) = $keep
                MATCH (drop) WHERE elementId(drop) = $drop
                SET keep += $props
                WITH keep, drop
                CALL apoc.refactor.mergeNodes([keep, drop], {properties: 'discard', mergeRels: true})
                YIELD node
                SET node.名称 = $name
                RETURN elementId(node) AS eid
                """,
                keep=action["keep"],
                drop=drop["eid"],
                props=combined,
                name=action["canonical"],
            )
            merged += 1
        if action["keep_name"] != action["canonical"]:
            session.run(
                "MATCH (n) WHERE elementId(n) = $eid SET n.名称 = $name",
                eid=action["keep"],
                name=action["canonical"],
            )
            renamed += 1
    return {"merged": merged, "renamed": renamed}


def run(driver: Any, *, apply_changes: bool) -> dict[str, Any]:
    with driver.session(database="neo4j") as session:
        property_actions = plan_property_rewrites(load_property_rows(session))
        node_actions = plan_node_merges(load_shared_nodes(session))
        stats = {
            "property_rewrites": len(property_actions),
            "node_groups": len(node_actions),
            "nodes_to_drop": sum(len(item["drop"]) for item in node_actions),
            "applied": False,
        }
        if apply_changes:
            stats["properties_written"] = apply_property_actions(session, property_actions)
            stats.update(apply_node_actions(session, node_actions))
            stats["applied"] = True
        stats["samples"] = {
            "properties": property_actions[:12],
            "nodes": node_actions,
        }
        return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:17687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "neo4j_password"))
    args = parser.parse_args()
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    driver.verify_connectivity()
    try:
        stats = run(driver, apply_changes=args.apply)
    finally:
        driver.close()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
