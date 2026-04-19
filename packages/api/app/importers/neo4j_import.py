"""提供导入记录到 Neo4j 的复用桥接能力。"""

from __future__ import annotations

from app.export.models import GraphWriteResult
from app.export.service import GraphWriter, Neo4jGraphWriter
from knowledge_model.import_records import GraphImportRecord


async def write_records_to_neo4j(
    records: list[GraphImportRecord],
    *,
    graph_writer: GraphWriter | None = None,
) -> GraphWriteResult:
    """把共享导入记录写入 Neo4j，并返回写入统计。"""

    writer = graph_writer or Neo4jGraphWriter()
    return await writer.write_records(records)
