"""导出活图并导入空库。neo4j-admin dump 会保留 db.propertyKeys() 幽灵英文键，不能用来清目录。"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from knowledge_model.graph_i18n import is_ascii_property_key, to_graph_properties


def _jsonable(value: object) -> object:
    if hasattr(value, "iso_format"):
        return value.iso_format()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _clean_props(props: dict[str, object]) -> dict[str, object]:
    cleaned: dict[str, object] = {}
    for key, value in props.items():
        if value is None or is_ascii_property_key(key):
            continue
        cleaned[key] = _jsonable(value)
    return to_graph_properties(cleaned)


def export_graph(driver: object, output: Path) -> dict[str, int]:
    nodes: list[dict[str, object]] = []
    rels: list[dict[str, object]] = []
    with driver.session(database="neo4j") as session:
        for index, row in enumerate(
            session.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props")
        ):
            nodes.append(
                {
                    "id": str(index),
                    "legacy_id": row["id"],
                    "labels": list(row["labels"]),
                    "props": _clean_props(dict(row["props"])),
                }
            )
        legacy_to_export = {node["legacy_id"]: node["id"] for node in nodes}
        for row in session.run(
            "MATCH (a)-[r]->(b) RETURN elementId(a) AS s, elementId(b) AS t, type(r) AS type, properties(r) AS props"
        ):
            rels.append(
                {
                    "s": legacy_to_export[row["s"]],
                    "t": legacy_to_export[row["t"]],
                    "type": row["type"],
                    "props": _clean_props(dict(row["props"])),
                }
            )
    payload = {"nodes": [{k: v for k, v in node.items() if k != "legacy_id"} for node in nodes], "rels": rels}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return {"nodes": len(nodes), "rels": len(rels)}


def _chunks(items: list[dict[str, object]], size: int) -> list[list[dict[str, object]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def import_graph(driver: object, source: Path) -> dict[str, int]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    nodes: list[dict[str, object]] = payload["nodes"]
    rels: list[dict[str, object]] = payload["rels"]
    id_map: dict[str, str] = {}
    with driver.session(database="neo4j") as session:
        for batch in _chunks(nodes, 200):
            rows = session.run(
                """
                UNWIND $batch AS row
                CALL apoc.create.node(row.labels, row.props) YIELD node
                RETURN row.id AS id, elementId(node) AS eid
                """,
                batch=batch,
            )
            for row in rows:
                id_map[row["id"]] = row["eid"]
        for batch in _chunks(rels, 200):
            resolved = [{"s": id_map[item["s"]], "t": id_map[item["t"]], "type": item["type"], "props": item["props"]} for item in batch]
            session.run(
                """
                UNWIND $batch AS row
                MATCH (a) WHERE elementId(a) = row.s
                MATCH (b) WHERE elementId(b) = row.t
                CALL apoc.create.relationship(a, row.type, row.props, b) YIELD rel
                RETURN count(rel) AS created
                """,
                batch=resolved,
            )
    return {"nodes": len(nodes), "rels": len(rels)}


def connect(uri: str, user: str, password: str) -> Any:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    return driver


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["export", "import"])
    parser.add_argument("--file", required=True)
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:17687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "neo4j_password"))
    args = parser.parse_args()
    driver = connect(args.uri, args.user, args.password)
    try:
        path = Path(args.file)
        stats = export_graph(driver, path) if args.action == "export" else import_graph(driver, path)
    finally:
        driver.close()
    print(json.dumps({"ok": True, "action": args.action, **stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
