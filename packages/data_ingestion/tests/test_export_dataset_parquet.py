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


def test_source_record_paths_splits_public_and_restricted(tmp_path):
    for source_id in ("published", "license-blocked"):
        path = tmp_path / "sources" / source_id / "processed" / "latest" / "records.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("{}\n", encoding="utf-8")
    catalog = Catalog.model_validate(
        {
            "dataset_id": "ticoAg/baicao-knowledge",
            "visibility": "private",
            "knowledge_model": "packages/knowledge_model",
            "updated_at": "2026-09-06",
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

    names = lambda paths: [path.parents[2].name for path in paths]
    assert names(source_record_paths(tmp_path, catalog)) == ["published", "license-blocked"]
    assert names(source_record_paths(tmp_path, catalog, tier="public")) == ["published"]
    assert names(source_record_paths(tmp_path, catalog, tier="restricted")) == ["license-blocked"]


def test_to_tables_stamps_license_fields():
    from data_ingestion.dataset_catalog import CatalogSource

    record = DatasetRecord(
        source_id="license-blocked",
        batch_id="batch",
        unit_id="unit",
        node_type="药材",
        node_name="人参",
        evidence_text="secret",
        properties={"raw_text": "full"},
    )
    meta = CatalogSource.model_validate(
        {
            "source_id": "license-blocked",
            "title": "blocked",
            "status": "imported",
            "kind": "graph_relations",
            "publish": False,
            "license_status": "unlicensed_upstream",
            "license": "unknown",
            "filter": {
                "source_provider": "github",
                "dataset_name": "blocked",
                "file_path": "x",
                "import_scope_key": "github:blocked",
            },
            "planned": {},
            "completed": {},
            "paths": {},
        }
    )
    records, _ = to_tables(
        [record],
        redact_source_text=True,
        source_meta={meta.source_id: meta},
    )
    row = records.to_pylist()[0]
    assert row["evidence_text"] is None
    assert row["release_tier"] == "restricted"
    assert row["license_status"] == "unlicensed_upstream"
    assert row["license"] == "unknown"

