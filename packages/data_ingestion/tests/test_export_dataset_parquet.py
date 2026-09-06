import json

import pytest

pytest.importorskip("pyarrow")

from data_ingestion.cli.export_dataset_parquet import records_from_tables, source_record_paths, to_tables
from data_ingestion.cli.import_dataset_neo4j import prepare_import_records
from data_ingestion.dataset_catalog import Catalog
from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.provenance import graph_node_props, slim_record


def _sample_record() -> DatasetRecord:
    return DatasetRecord(
        source_id="tcm-mkg",
        batch_id="batch",
        unit_id="方剂:测试方",
        node_type="方剂",
        node_name="测试方",
        evidence_text="黄芪30g",
        evidence_refs=["证据:tcm-mkg:1"],
        prompt_hash="sha256:abc",
        import_scope_key="zenodo:tcm-mkg",
        properties={"raw_text": "full source", "latin_name": "GINSENG"},
        edges=[
            DatasetEdge(
                type="组成药材",
                target="黄芪",
                properties={"dosage": "30g", "dosage_ratio": "0.5", "evidence_ref": "row:1"},
            )
        ],
    )


def test_export_keeps_evidence_and_edge_props_but_strips_full_source():
    records, edges = to_tables([_sample_record()], redact_source_text=True)
    row = records.to_pylist()[0]
    edge = edges.to_pylist()[0]

    assert row["evidence_text"] == "黄芪30g"
    assert json.loads(row["properties_json"]) == {"latin_name": "GINSENG"}
    assert edge["dosage"] == "30g"
    assert edge["dosage_ratio"] == "0.5"
    assert edge["evidence_ref"] == "row:1"


def test_parquet_round_trip_matches_jsonl_graph_payload():
    original = _sample_record()
    records, edges = to_tables([original], redact_source_text=True)
    restored = records_from_tables(records, edges)
    assert len(restored) == 1

    from_jsonl = slim_record(
        original, prompt_hash=original.prompt_hash or "sha256:abc", import_scope_key=original.import_scope_key
    )
    from_parquet = prepare_import_records(restored)[0]
    assert graph_node_props(from_parquet) == graph_node_props(from_jsonl)
    assert from_parquet.evidence_text == from_jsonl.evidence_text
    assert from_parquet.evidence_refs == from_jsonl.evidence_refs
    assert from_parquet.import_scope_key == from_jsonl.import_scope_key
    assert [(edge.type, edge.target, edge.properties) for edge in from_parquet.edges] == [
        (edge.type, edge.target, edge.properties) for edge in from_jsonl.edges
    ]


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
    assert row["evidence_text"] == "secret"
    assert row["release_tier"] == "restricted"
    assert row["license_status"] == "unlicensed_upstream"
    assert row["license"] == "unknown"
