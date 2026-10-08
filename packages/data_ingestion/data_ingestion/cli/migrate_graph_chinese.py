"""把现有 Neo4j 标签、属性键、状态/来源值改成中文。"""

from __future__ import annotations

import argparse
import json
import os

from graph_schema.constants import LEGACY_ENGLISH_NEO4J_LABELS, NodeType
from graph_schema.graph_i18n import (
    PROPERTY_EN_TO_ZH,
    PROVIDER_VALUE_EN_TO_ZH,
    SCOPE_VALUE_EN_TO_ZH,
    SOURCE_VALUE_EN_TO_ZH,
    STATUS_EN_TO_ZH,
)


def run(driver: object) -> dict[str, int]:
    stats = {"labels": 0, "node_props": 0, "rel_props": 0, "values": 0}
    with driver.session(database="neo4j") as session:
        for node_type, english in LEGACY_ENGLISH_NEO4J_LABELS.items():
            session.run(
                "CALL apoc.refactor.rename.label($old, $new)",
                old=english,
                new=node_type.value,
            )
            stats["labels"] += 1
        for english, chinese in PROPERTY_EN_TO_ZH.items():
            session.run(
                "CALL apoc.refactor.rename.nodeProperty($old, $new)",
                old=english,
                new=chinese,
            )
            session.run(
                "CALL apoc.refactor.rename.typeProperty($old, $new)",
                old=english,
                new=chinese,
            )
            stats["node_props"] += 1
            stats["rel_props"] += 1
        for old, new in STATUS_EN_TO_ZH.items():
            session.run("MATCH (n) WHERE n.状态 = $old SET n.状态 = $new", old=old, new=new)
            session.run("MATCH ()-[r]->() WHERE r.状态 = $old SET r.状态 = $new", old=old, new=new)
            stats["values"] += 1
        for old, new in SOURCE_VALUE_EN_TO_ZH.items():
            session.run("MATCH (n) WHERE n.来源 = $old SET n.来源 = $new", old=old, new=new)
            session.run("MATCH (n) WHERE n.导入源 = $old SET n.导入源 = $new", old=old, new=new)
            session.run(
                """
                MATCH (n)
                WHERE n.导入源列表 IS NOT NULL
                SET n.导入源列表 = [x IN n.导入源列表 | CASE WHEN x = $old THEN $new ELSE x END]
                """,
                old=old,
                new=new,
            )
            session.run("MATCH ()-[r]->() WHERE r.导入源 = $old SET r.导入源 = $new", old=old, new=new)
        for old, new in SCOPE_VALUE_EN_TO_ZH.items():
            session.run("MATCH (n) WHERE n.导入范围键 = $old SET n.导入范围键 = $new", old=old, new=new)
            session.run(
                """
                MATCH (n)
                WHERE n.导入范围键列表 IS NOT NULL
                SET n.导入范围键列表 = [x IN n.导入范围键列表 | CASE WHEN x = $old THEN $new ELSE x END]
                """,
                old=old,
                new=new,
            )
            session.run("MATCH ()-[r]->() WHERE r.导入范围键 = $old SET r.导入范围键 = $new", old=old, new=new)
        for old, new in PROVIDER_VALUE_EN_TO_ZH.items():
            session.run("MATCH (n) WHERE n.来源提供方 = $old SET n.来源提供方 = $new", old=old, new=new)
            session.run("MATCH ()-[r]->() WHERE r.来源提供方 = $old SET r.来源提供方 = $new", old=old, new=new)
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", default=os.environ.get("NEO4J_URI", "bolt://localhost:17687"))
    parser.add_argument("--user", default=os.environ.get("NEO4J_USERNAME", "neo4j"))
    parser.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD", "neo4j_password"))
    args = parser.parse_args()
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    driver.verify_connectivity()
    try:
        stats = run(driver)
    finally:
        driver.close()
    print(json.dumps({"ok": True, **stats}, ensure_ascii=False))


if __name__ == "__main__":
    main()
