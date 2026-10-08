import json

import pytest

from app.exporters.jsonl_exporter import JSONLExporter
from app.importers import EdgeRecord, GraphRecord
from app.importers.jsonl_importer import JSONLImporter
from graph_schema.constants import EdgeType, NodeType
from graph_schema.import_records import GraphImportEdge, GraphImportRecord

pytestmark = pytest.mark.contract


def test_jsonl_importer_returns_shared_record(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text(
        json.dumps(
            {
                "node_type": "Herb",
                "node_name": "陈皮",
                "source": "中国药典",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    record = next(iter(JSONLImporter().load(str(path))))

    assert isinstance(record, GraphImportRecord)


def test_jsonl_exporter_accepts_shared_record(tmp_path):
    path = tmp_path / "records.jsonl"
    record = GraphImportRecord(
        node_type=NodeType.HERB,
        node_name="陈皮",
        source="中国药典",
        edges=[
            GraphImportEdge(
                type=EdgeType.HAS_EFFICACY,
                target="理气",
            )
        ],
    )

    stats = JSONLExporter().export([record], str(path))

    assert stats.success == 1
    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload["node_type"] == "药材"


def test_importers_init_re_exports_shared_record_types():
    assert GraphRecord is GraphImportRecord
    assert EdgeRecord is GraphImportEdge
