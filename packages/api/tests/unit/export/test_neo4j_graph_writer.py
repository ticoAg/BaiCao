"""覆盖 Neo4jGraphWriter 对数据集 scope 关系的写入行为。"""

from app.export.service import Neo4jGraphWriter
from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord


async def test_neo4j_graph_writer_merges_relationships_by_import_scope(monkeypatch):
    """验证带 import_scope_key 的边会用 scope 属性参与 MERGE。"""

    calls: list[tuple[str, dict]] = []

    async def fake_cypher_query(query: str, params: dict | None = None):
        calls.append((query, params or {}))
        return [], []

    monkeypatch.setattr("app.export.service.cypher_query", fake_cypher_query)

    await Neo4jGraphWriter().write_records(
        [
            GraphImportRecord(
                node_type=NodeType.HERB,
                node_name="一枝黄花",
                source="huggingface",
                edges=[
                    GraphImportEdge(
                        type=EdgeType.HAS_PREPARED_FORM,
                        target="一枝黄花饮片",
                        properties={
                            "import_scope_key": "huggingface|dataset|file.txt",
                            "dataset_name": "dataset",
                        },
                    )
                ],
            )
        ]
    )

    relationship_query, relationship_params = calls[1]
    assert "import_scope_key: $import_scope_key" in relationship_query
    assert relationship_params["import_scope_key"] == "huggingface|dataset|file.txt"
    assert relationship_params["props"]["dataset_name"] == "dataset"
