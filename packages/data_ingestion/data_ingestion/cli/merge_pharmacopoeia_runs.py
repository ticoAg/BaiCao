"""合并药典 ingest run，并打上 source_id / batch_id。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.dataset_records import DatasetRecord, stamp_import_record, utc_now


SOURCE_ID = "national-standard-2022-pharmacopoeia"
PROCESSOR = "pharmacopoeia_ingest"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def iter_run_dirs(root: Path) -> list[Path]:
    return sorted(
        path.parent
        for path in root.glob("*/manual-run/graph_import_records.jsonl")
        if path.is_file()
    )


def load_run(run_dir: Path) -> list[DatasetRecord]:
    batch_id = f"2026-04-19-pharmacopoeia-{run_dir.parent.name}"
    records_path = run_dir / "graph_import_records.jsonl"
    records: list[DatasetRecord] = []
    for line in records_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        properties = raw.get("properties") or {}
        unit_title = properties.get("entry_title") or raw.get("node_name")
        unit_id = f"entry:{unit_title}"
        records.append(
            stamp_import_record(
                raw,
                source_id=SOURCE_ID,
                batch_id=batch_id,
                unit_id=str(unit_id),
                unit_title=str(unit_title) if unit_title else None,
                processor=PROCESSOR,
                extracted_at=utc_now(),
            )
        )
    return records


def dedupe(records: list[DatasetRecord]) -> list[DatasetRecord]:
    merged: dict[tuple[str, str, str], DatasetRecord] = {}
    for record in records:
        key = (record.node_type, record.node_name, record.unit_id)
        merged[key] = record
    return list(merged.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=repo_root() / "packages/data_ingestion/tmp/pharmacopoeia-ingestion",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=repo_root()
        / "datasets/baicao-knowledge/sources/national-standard-2022-pharmacopoeia/processed/latest/records.jsonl",
    )
    args = parser.parse_args()
    run_dirs = iter_run_dirs(args.runs_root)
    if not run_dirs:
        raise SystemExit(f"no runs under {args.runs_root}")
    records: list[DatasetRecord] = []
    for run_dir in run_dirs:
        records.extend(load_run(run_dir))
    records = dedupe(records)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "\n".join(record.model_dump_json(ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    print(f"runs={len(run_dirs)} records={len(records)} out={args.out}")


if __name__ == "__main__":
    main()
