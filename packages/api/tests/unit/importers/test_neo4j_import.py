"""覆盖 JSONL 导入记录到 Neo4j 写入器的桥接逻辑。"""

from app.export.models import GraphWriteResult
from app.importers.neo4j_import import write_records_to_neo4j
from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord


class DummyGraphWriter:
    """记录收到的导入记录，并返回固定写入统计。"""

    def __init__(self) -> None:
        self.received: list[GraphImportRecord] = []

    async def write_records(self, records: list[GraphImportRecord]) -> GraphWriteResult:
        self.received.extend(records)
        return GraphWriteResult(
            nodes_written=len(records),
            edges_written=sum(len(record.edges) for record in records),
        )


async def test_write_records_to_neo4j_uses_graph_writer_and_returns_stats():
    """验证桥接函数会把合法记录交给图写入器，并返回节点/边统计。"""

    writer = DummyGraphWriter()
    records = [
        GraphImportRecord(
            node_type=NodeType.HERB,
            node_name="一枝黄花",
            source="中国药典",
            edges=[GraphImportEdge(type=EdgeType.SUPPORTED_BY, target="一枝黄花条目证据")],
        ),
        GraphImportRecord(
            node_type=NodeType.EVIDENCE,
            node_name="一枝黄花条目证据",
            source="中国药典",
        ),
    ]

    result = await write_records_to_neo4j(records, graph_writer=writer)

    assert [record.node_name for record in writer.received] == ["一枝黄花", "一枝黄花条目证据"]
    assert result.nodes_written == 2
    assert result.edges_written == 1
