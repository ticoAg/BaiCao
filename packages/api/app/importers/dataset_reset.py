"""提供数据集级和快照级图谱重置能力。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.kg.db import cypher_rows
from graph_schema.constants import EdgeType, to_neo4j_label
from graph_schema.import_records import GraphImportRecord


class GraphResetResult(BaseModel):
    """记录一次图谱重置删除的节点和关系数量。"""

    nodes_deleted: int = Field(default=0, description="删除节点数量")
    relationships_deleted: int = Field(default=0, description="删除关系数量")

    model_config = ConfigDict(use_enum_values=False)


def _deleted_count(rows: list[dict]) -> int:
    """从 Cypher 返回行中读取 deleted 计数。"""

    return int(rows[0].get("deleted", 0)) if rows else 0


async def reset_graph_from_records(records: list[GraphImportRecord]) -> GraphResetResult:
    """按快照中的记录精确删除关系，并删除变成孤立的快照节点。"""

    relationships_deleted = 0
    nodes_deleted = 0
    for record in records:
        for edge in record.edges:
            rel_type = EdgeType(getattr(edge.type, "value", edge.type)).value
            rows = await cypher_rows(
                f"""
                MATCH (source {{name: $source_name}})-[r:{rel_type}]->(target {{name: $target_name}})
                WITH collect(r) AS rels, count(r) AS deleted
                FOREACH (r IN rels | DELETE r)
                RETURN deleted
                """,
                {"source_name": record.node_name, "target_name": edge.target},
            )
            relationships_deleted += _deleted_count(rows)

    for record in records:
        if record.node_type is None:
            continue
        label = to_neo4j_label(record.node_type)
        rows = await cypher_rows(
            f"""
            MATCH (n:{label} {{name: $name}})
            WHERE NOT (n)--()
            WITH collect(n) AS nodes, count(n) AS deleted
            FOREACH (n IN nodes | DELETE n)
            RETURN deleted
            """,
            {"name": record.node_name},
        )
        nodes_deleted += _deleted_count(rows)

    return GraphResetResult(nodes_deleted=nodes_deleted, relationships_deleted=relationships_deleted)


async def reset_dataset_graph(
    *,
    provider: str,
    dataset: str,
    file_path: str | None = None,
) -> GraphResetResult:
    """按导入 scope 清理某个数据集或数据集内单文件的图谱关系与孤立节点。"""

    scope_filter = (
        "r.source_provider = $provider AND r.dataset_name = $dataset "
        "AND ($file_path IS NULL OR r.file_path = $file_path)"
    )
    node_filter = (
        "n.source_provider = $provider AND n.dataset_name = $dataset "
        "AND ($file_path IS NULL OR n.file_path = $file_path)"
    )
    params = {"provider": provider, "dataset": dataset, "file_path": file_path}

    relationship_rows = await cypher_rows(
        f"""
        MATCH ()-[r]->()
        WHERE {scope_filter}
        WITH collect(r) AS rels, count(r) AS deleted
        FOREACH (r IN rels | DELETE r)
        RETURN deleted
        """,
        params,
    )
    evidence_rows = await cypher_rows(
        f"""
        MATCH (n:Evidence)
        WHERE {node_filter}
        WITH collect(n) AS nodes, count(n) AS deleted
        FOREACH (n IN nodes | DETACH DELETE n)
        RETURN deleted
        """,
        params,
    )
    orphan_rows = await cypher_rows(
        f"""
        MATCH (n)
        WHERE {node_filter} AND NOT (n)--()
        WITH collect(n) AS nodes, count(n) AS deleted
        FOREACH (n IN nodes | DELETE n)
        RETURN deleted
        """,
        params,
    )

    return GraphResetResult(
        nodes_deleted=_deleted_count(evidence_rows) + _deleted_count(orphan_rows),
        relationships_deleted=_deleted_count(relationship_rows),
    )
