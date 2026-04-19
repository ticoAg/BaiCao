"""覆盖数据集级图谱重置能力。"""

from app.importers.dataset_reset import reset_dataset_graph, reset_graph_from_records
from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord


async def test_reset_graph_from_records_deletes_snapshot_edges_then_orphan_nodes(monkeypatch):
    """验证基于快照重置时，会先删边再删孤立节点。"""

    calls: list[tuple[str, dict]] = []

    async def fake_cypher_rows(query: str, params: dict | None = None):
        calls.append((query, params or {}))
        return [{"deleted": 1}]

    monkeypatch.setattr("app.importers.dataset_reset.cypher_rows", fake_cypher_rows)

    result = await reset_graph_from_records(
        [
            GraphImportRecord(
                node_type=NodeType.HERB,
                node_name="一枝黄花",
                source="huggingface",
                edges=[GraphImportEdge(type=EdgeType.HAS_PREPARED_FORM, target="一枝黄花饮片")],
            ),
            GraphImportRecord(
                node_type=NodeType.PREPARED_HERB,
                node_name="一枝黄花饮片",
                source="huggingface",
            ),
        ]
    )

    assert result.relationships_deleted == 1
    assert result.nodes_deleted == 2
    assert "DELETE r" in calls[0][0]
    assert calls[0][1]["source_name"] == "一枝黄花"
    assert calls[0][1]["target_name"] == "一枝黄花饮片"


async def test_reset_dataset_graph_deletes_scoped_relationships_and_orphans(monkeypatch):
    """验证按数据集 scope 重置时，会使用 provider/dataset/file_path 定位。"""

    calls: list[tuple[str, dict]] = []

    async def fake_cypher_rows(query: str, params: dict | None = None):
        calls.append((query, params or {}))
        return [{"deleted": 2}]

    monkeypatch.setattr("app.importers.dataset_reset.cypher_rows", fake_cypher_rows)

    result = await reset_dataset_graph(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
    )

    assert result.relationships_deleted == 2
    assert result.nodes_deleted == 4
    assert all(call[1]["provider"] == "huggingface" for call in calls)
    assert all(call[1]["dataset"] == "ZJUFanLab/TCMChat-dataset-600k" for call in calls)
