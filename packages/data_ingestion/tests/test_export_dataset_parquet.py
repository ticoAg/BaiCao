import json

import pytest

pytest.importorskip("pyarrow")

from data_ingestion.cli.export_dataset_parquet import source_record_paths, to_tables
from data_ingestion.dataset_catalog import Catalog
from data_ingestion.dataset_records import DatasetRecord


def test_public_table_redacts_source_text_but_keeps_structured_properties():
    record = DatasetRecord(
        source_id="source",
        batch_id="batch",
        unit_id="unit",
        node_type="证据",
        node_name="evidence",
        evidence_text="copyrighted excerpt",
        properties={"raw_text": "full source", "latin_name": "GINSENG"},
    )

    records, _ = to_tables([record], redact_source_text=True)
    row = records.to_pylist()[0]

    assert row["evidence_text"] is None
    assert json.loads(row["properties_json"]) == {"latin_name": "GINSENG"}


def test_source_record_paths_fail_closed_for_unpublished_sources(tmp_path):
    for source_id in ("published", "license-blocked"):
        path = tmp_path / "sources" / source_id / "processed" / "latest" / "records.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("", encoding="utf-8")
    catalog = Catalog.model_validate(
        {
            "dataset_id": "ticoAg/baicao-knowledge",
            "visibility": "public",
            "knowledge_model": "packages/knowledge_model",
            "updated_at": "2026-08-19",
            "sources": [
                {
                    "source_id": source_id,
                    "title": source_id,
                    "status": "cleaned",
                    "kind": "graph_relations",
                    "publish": source_id == "published",
                    "filter": {
                        "source_provider": "github",
                        "dataset_name": source_id,
                        "file_path": "relations.json",
                        "import_scope_key": f"github:{source_id}",
                    },
                    "planned": {},
                    "completed": {},
                    "paths": {},
                }
                for source_id in ("published", "license-blocked")
            ],
        }
    )

    assert [path.parents[2].name for path in source_record_paths(tmp_path, catalog)] == [
        "published"
    ]
