"""把各源 latest JSONL 拼成 HF Viewer 用的 records/edges Parquet。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from data_ingestion.dataset_catalog import (
    RELEASE_PUBLIC,
    RELEASE_RESTRICTED,
    Catalog,
    CatalogSource,
    ReleaseTier,
    load_catalog,
)
from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.entity_identity import sanitize_record
from data_ingestion.provenance import GRAPH_EDGE_PROPS

# 全书/长正文键仍不进发布表；入图用的证据片段走顶栏 evidence_text。
FULL_SOURCE_PROPERTY_KEYS = {
    "raw_text",
    "source_text",
    "content",
    "text",
}

EMPTY_RECORD_ROW = {
    "source_id": "",
    "batch_id": "",
    "unit_id": "",
    "node_type": "",
    "node_name": "",
    "prompt_hash": "",
    "import_scope_key": "",
    "evidence_refs": [],
    "evidence_text": None,
    "properties_json": "{}",
    "release_tier": "",
    "license_status": "",
    "license": "",
}

EMPTY_EDGE_ROW = {
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
    "dosage_ratio": None,
    "evidence_ref": None,
    "release_tier": "",
    "license_status": "",
    "license": "",
}

RECORD_SCHEMA = pa.schema(
    [
        ("source_id", pa.string()),
        ("batch_id", pa.string()),
        ("unit_id", pa.string()),
        ("node_type", pa.string()),
        ("node_name", pa.string()),
        ("prompt_hash", pa.string()),
        ("import_scope_key", pa.string()),
        ("evidence_refs", pa.list_(pa.string())),
        ("evidence_text", pa.string()),
        ("properties_json", pa.string()),
        ("release_tier", pa.string()),
        ("license_status", pa.string()),
        ("license", pa.string()),
    ]
)
EDGE_SCHEMA = pa.schema(
    [
        ("source_id", pa.string()),
        ("batch_id", pa.string()),
        ("unit_id", pa.string()),
        ("from_node_type", pa.string()),
        ("from_node_name", pa.string()),
        ("edge_type", pa.string()),
        ("target", pa.string()),
        ("prompt_hash", pa.string()),
        ("import_scope_key", pa.string()),
        ("dosage", pa.string()),
        ("dosage_ratio", pa.string()),
        ("evidence_ref", pa.string()),
        ("release_tier", pa.string()),
        ("license_status", pa.string()),
        ("license", pa.string()),
    ]
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_jsonl(path: Path) -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(DatasetRecord.model_validate(json.loads(line)))
    return records


def source_jsonl_path(dataset_root: Path, source_id: str) -> Path:
    return dataset_root / "sources" / source_id / "processed" / "latest" / "records.jsonl"


def source_record_paths(
    dataset_root: Path, catalog: Catalog, *, tier: ReleaseTier | None = None
) -> list[Path]:
    selected: list[Path] = []
    for source in catalog.sources:
        if tier is not None and source.release_tier != tier:
            continue
        path = source_jsonl_path(dataset_root, source.source_id)
        if path.is_file():
            selected.append(path)
    return selected


def data_dir_for(dataset_root: Path, tier: ReleaseTier) -> Path:
    return dataset_root / "data" / tier


def _optional_str(value: object) -> str | None:
    if value in (None, "", [], {}):
        return None
    return str(value)


def to_tables(
    records: list[DatasetRecord],
    *,
    redact_source_text: bool = False,
    source_meta: dict[str, CatalogSource] | None = None,
) -> tuple[pa.Table, pa.Table]:
    record_rows = []
    edge_rows = []
    for record in records:
        record = sanitize_record(record)
        meta = (source_meta or {}).get(record.source_id)
        release_tier = meta.release_tier if meta else ""
        license_status = meta.license_status if meta else ""
        license_name = meta.license if meta else ""
        properties = dict(record.properties or {})
        if redact_source_text:
            for key in FULL_SOURCE_PROPERTY_KEYS:
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
                "evidence_refs": list(record.evidence_refs or []),
                "evidence_text": record.evidence_text or None,
                "properties_json": json.dumps(properties, ensure_ascii=False),
                "release_tier": release_tier,
                "license_status": license_status,
                "license": license_name,
            }
        )
        for edge in record.edges:
            edge_props = dict(edge.properties or {})
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
                    "dosage": _optional_str(edge_props.get("dosage")),
                    "dosage_ratio": _optional_str(edge_props.get("dosage_ratio")),
                    "evidence_ref": _optional_str(edge_props.get("evidence_ref")),
                    "release_tier": release_tier,
                    "license_status": license_status,
                    "license": license_name,
                }
            )
    return pa.Table.from_pylist(record_rows or [EMPTY_RECORD_ROW], schema=RECORD_SCHEMA), pa.Table.from_pylist(
        edge_rows or [EMPTY_EDGE_ROW], schema=EDGE_SCHEMA
    )


def records_from_tables(record_table: pa.Table, edge_table: pa.Table) -> list[DatasetRecord]:
    """把发布表拼回 DatasetRecord，字段覆盖 slim_record / 入图所用的全部键。"""
    edges_by_key: dict[tuple[str, str, str, str, str], list[DatasetEdge]] = {}
    for row in edge_table.to_pylist():
        source_id = row.get("source_id") or ""
        if not source_id:
            continue
        key = (
            source_id,
            row.get("batch_id") or "",
            row.get("unit_id") or "",
            row.get("from_node_type") or "",
            row.get("from_node_name") or "",
        )
        properties = {
            name: value
            for name in GRAPH_EDGE_PROPS
            if (value := _optional_str(row.get(name))) is not None
        }
        edges_by_key.setdefault(key, []).append(
            DatasetEdge(type=row["edge_type"], target=row["target"], properties=properties)
        )
    records: list[DatasetRecord] = []
    for row in record_table.to_pylist():
        source_id = row.get("source_id") or ""
        if not source_id:
            continue
        properties = json.loads(row.get("properties_json") or "{}")
        if not isinstance(properties, dict):
            properties = {}
        record = DatasetRecord(
            source_id=source_id,
            batch_id=row.get("batch_id") or "",
            unit_id=row.get("unit_id") or "",
            node_type=row["node_type"],
            node_name=row["node_name"],
            evidence_refs=list(row.get("evidence_refs") or []),
            evidence_text=row.get("evidence_text") or None,
            prompt_hash=row.get("prompt_hash") or None,
            import_scope_key=row.get("import_scope_key") or None,
            properties=properties,
            edges=edges_by_key.get(
                (
                    source_id,
                    row.get("batch_id") or "",
                    row.get("unit_id") or "",
                    row.get("node_type") or "",
                    row.get("node_name") or "",
                ),
                [],
            ),
        )
        record.validate_types()
        records.append(record)
    return records


def _write_tier(
    dataset_root: Path,
    catalog: Catalog,
    *,
    tier: ReleaseTier,
    redact_source_text: bool,
    source_meta: dict[str, CatalogSource],
) -> dict[str, object]:
    tables: list[tuple[pa.Table, pa.Table]] = []
    record_count = 0
    for path in source_record_paths(dataset_root, catalog, tier=tier):
        records = load_jsonl(path)
        if not records:
            continue
        record_count += len(records)
        local_records, local_edges = to_tables(
            records, redact_source_text=redact_source_text, source_meta=source_meta
        )
        pq.write_table(local_records, path.with_name("records.parquet"))
        pq.write_table(local_edges, path.with_name("edges.parquet"))
        tables.append((local_records, local_edges))
    out_dir = data_dir_for(dataset_root, tier)
    out_dir.mkdir(parents=True, exist_ok=True)
    record_parquet = out_dir / "records.parquet"
    edge_parquet = out_dir / "edges.parquet"
    if not tables:
        empty_records, empty_edges = to_tables([], redact_source_text=redact_source_text)
        pq.write_table(empty_records, record_parquet)
        pq.write_table(empty_edges, edge_parquet)
        return {
            "tier": tier,
            "records": 0,
            "record_parquet": str(record_parquet),
            "edge_parquet": str(edge_parquet),
        }
    record_table = pa.concat_tables([item[0] for item in tables])
    edge_table = pa.concat_tables([item[1] for item in tables])
    pq.write_table(record_table, record_parquet)
    pq.write_table(edge_table, edge_parquet)
    return {
        "tier": tier,
        "records": record_count,
        "record_parquet": str(record_parquet),
        "edge_parquet": str(edge_parquet),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=repo_root() / "datasets/baicao-knowledge")
    parser.add_argument(
        "--tier",
        choices=(RELEASE_PUBLIC, RELEASE_RESTRICTED, "all"),
        default="all",
    )
    args = parser.parse_args()
    catalog = load_catalog(args.dataset_root / "catalog.json")
    source_meta = {source.source_id: source for source in catalog.sources}
    tiers: tuple[ReleaseTier, ...]
    if args.tier == "all":
        tiers = (RELEASE_PUBLIC, RELEASE_RESTRICTED)
    else:
        tiers = (args.tier,)
    reports = []
    for tier in tiers:
        reports.append(
            _write_tier(
                args.dataset_root,
                catalog,
                tier=tier,
                redact_source_text=True,
                source_meta=source_meta,
            )
        )
    if args.tier != RELEASE_RESTRICTED and not any(item["records"] for item in reports if item["tier"] == RELEASE_PUBLIC):
        if RELEASE_PUBLIC in tiers:
            raise SystemExit(f"no public records.jsonl under {args.dataset_root}")
    print(json.dumps({"visibility": catalog.visibility, "tiers": reports}, ensure_ascii=False))


if __name__ == "__main__":
    main()
