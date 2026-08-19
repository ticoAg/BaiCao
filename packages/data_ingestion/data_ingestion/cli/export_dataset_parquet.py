"""把各源 latest JSONL 拼成 HF Viewer 用的 records/edges Parquet。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from data_ingestion.dataset_catalog import Catalog, load_catalog
from data_ingestion.dataset_records import DatasetRecord

PUBLIC_REDACTED_PROPERTY_KEYS = {
    "raw_text",
    "evidence_text",
    "source_text",
    "content",
    "text",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_jsonl(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(DatasetRecord.model_validate(json.loads(line)))
    return records


def source_record_paths(dataset_root: Path, catalog: Catalog) -> list[Path]:
    publishable = {source.source_id for source in catalog.sources if source.publish}
    return [
        path
        for path in sorted(dataset_root.glob("sources/*/processed/latest/records.jsonl"))
        if path.parents[2].name in publishable
    ]


def to_tables(
    records: list[DatasetRecord], *, redact_source_text: bool = False
) -> tuple[pa.Table, pa.Table]:
    record_rows = []
    edge_rows = []
    for record in records:
        properties = dict(record.properties or {})
        if redact_source_text:
            for key in PUBLIC_REDACTED_PROPERTY_KEYS:
                properties.pop(key, None)
        record_rows.append(
            {
                "source_id": record.source_id,
                "batch_id": record.batch_id,
                "unit_id": record.unit_id,
                "node_type": record.node_type,
                "node_name": record.node_name,
                "prompt_hash": record.prompt_hash,
                "import_scope_key": record.import_scope_key,
                "evidence_refs": record.evidence_refs,
                "evidence_text": None if redact_source_text else record.evidence_text,
                "properties_json": json.dumps(properties, ensure_ascii=False),
            }
        )
        for edge in record.edges:
            edge_rows.append(
                {
                    "source_id": record.source_id,
                    "batch_id": record.batch_id,
                    "unit_id": record.unit_id,
                    "from_node_type": record.node_type,
                    "from_node_name": record.node_name,
                    "edge_type": edge.type,
                    "target": edge.target,
                    "prompt_hash": record.prompt_hash,
                    "import_scope_key": record.import_scope_key,
                    "dosage": (edge.properties or {}).get("dosage"),
                }
            )
    return pa.Table.from_pylist(record_rows), pa.Table.from_pylist(edge_rows or [
        {
            "source_id": "",
            "batch_id": "",
            "unit_id": "",
            "from_node_type": "",
            "from_node_name": "",
            "edge_type": "",
            "target": "",
            "prompt_hash": "",
            "import_scope_key": "",
            "dosage": None,
        }
    ])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=repo_root() / "datasets/baicao-knowledge")
    args = parser.parse_args()
    catalog = load_catalog(args.dataset_root / "catalog.json")
    redact_source_text = catalog.visibility == "public"
    records: list[DatasetRecord] = []
    for path in source_record_paths(args.dataset_root, catalog):
        records.extend(load_jsonl(path))
        local_records, local_edges = to_tables(
            load_jsonl(path), redact_source_text=redact_source_text
        )
        pq.write_table(local_records, path.with_name("records.parquet"))
        pq.write_table(local_edges, path.with_name("edges.parquet"))
    if not records:
        raise SystemExit(f"no records.jsonl under {args.dataset_root}")
    data_dir = args.dataset_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    record_table, edge_table = to_tables(records, redact_source_text=redact_source_text)
    pq.write_table(record_table, data_dir / "records.parquet")
    pq.write_table(edge_table, data_dir / "edges.parquet")
    print(
        json.dumps(
            {
                "records": len(records),
                "visibility": catalog.visibility,
                "source_text_redacted": redact_source_text,
                "record_parquet": str(data_dir / "records.parquet"),
                "edge_parquet": str(data_dir / "edges.parquet"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
