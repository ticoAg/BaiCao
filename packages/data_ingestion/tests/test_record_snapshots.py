"""覆盖图谱导入记录快照的扁平化与落盘行为。"""

import json

from data_ingestion.record_snapshots import flatten_graph_import_records, write_graph_import_records_jsonl
from data_ingestion.bundles import UnifiedGraphBundle
from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord


def test_flatten_graph_import_records_collects_records_from_multiple_bundles():
    """验证多个 bundle 中的 GraphImportRecord 会按顺序展开。"""

    herb_record = GraphImportRecord(
        node_type=NodeType.HERB,
        node_name="一枝黄花",
        source="huggingface",
        edges=[GraphImportEdge(type=EdgeType.SUPPORTED_BY, target="一枝黄花条目证据")],
    )
    evidence_record = GraphImportRecord(
        node_type=NodeType.EVIDENCE,
        node_name="一枝黄花条目证据",
        source="huggingface",
    )

    records = flatten_graph_import_records(
        [
            UnifiedGraphBundle(records=[herb_record]),
            UnifiedGraphBundle(records=[evidence_record]),
        ]
    )

    assert [record.node_name for record in records] == ["一枝黄花", "一枝黄花条目证据"]


def test_write_graph_import_records_jsonl_persists_shared_record_schema(tmp_path):
    """验证导入记录快照会以共享 GraphImportRecord schema 写成 JSONL。"""

    path = tmp_path / "graph_import_records.jsonl"
    records = [
        GraphImportRecord(
            node_type=NodeType.HERB,
            node_name="丁公藤",
            source="huggingface",
            properties={"usage_text": "3～9g"},
        )
    ]

    write_graph_import_records_jsonl(path, records)

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["node_type"] == "药材"
    assert payload["node_name"] == "丁公藤"
    assert payload["properties"]["usage_text"] == "3～9g"
