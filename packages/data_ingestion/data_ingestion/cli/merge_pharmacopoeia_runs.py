"""合并药典 ingest run，并打上 source_id / batch_id。后写覆盖同名节点。"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetRecord, compute_stats, stamp_import_record
from data_ingestion.provenance import prompt_hash_for, scope_key_for


SOURCE_ID = "national-standard-2022-pharmacopoeia"
PROCESSOR = "pharmacopoeia_ingest"
PROMPT_FILE = (
    Path(__file__).resolve().parents[1]
    / "processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/prompts.py"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


@dataclass
class MergeResult:
    records: list[DatasetRecord]
    entries_succeeded: int
    entries_failed: int
    failed_entries: list[dict[str, Any]] = field(default_factory=list)
    run_dirs: list[Path] = field(default_factory=list)


def iter_run_dirs(root: Path) -> list[Path]:
    found = [
        path.parent
        for path in root.glob("*/manual-run/graph_import_records.jsonl")
        if path.is_file()
    ]

    def sort_key(run_dir: Path) -> tuple[str, str]:
        summary_path = run_dir / "summary.json"
        generated = ""
        if summary_path.is_file():
            generated = str(json.loads(summary_path.read_text(encoding="utf-8")).get("generated_at") or "")
        return (generated, str(run_dir))

    return sorted(found, key=sort_key)


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
                prompt_hash=prompt_hash_for(PROMPT_FILE) if PROMPT_FILE.is_file() else None,
                import_scope_key=scope_key_for(SOURCE_ID),
            )
        )
    return records


def collect_entry_outcomes(run_dirs: list[Path]) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for run_dir in run_dirs:
        path = run_dir / "validated_extractions.jsonl"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            key = item.get("entry_key")
            if not key:
                continue
            outcomes[str(key)] = item
    return outcomes


def dedupe(records: list[DatasetRecord]) -> list[DatasetRecord]:
    merged: dict[tuple[str, str, str], DatasetRecord] = {}
    for record in records:
        key = (record.node_type, record.node_name, record.source or SOURCE_ID)
        merged[key] = record
    return list(merged.values())


def merge_runs(runs_root: Path) -> MergeResult:
    run_dirs = iter_run_dirs(runs_root)
    if not run_dirs:
        raise ValueError(f"no runs under {runs_root}")
    records: list[DatasetRecord] = []
    for run_dir in run_dirs:
        records.extend(load_run(run_dir))
    records = dedupe(records)
    outcomes = collect_entry_outcomes(run_dirs)
    failed = [
        {
            "entry_key": key,
            "entry_title": item.get("entry_title"),
            "status": "unrecoverable",
            "last_status": item.get("status"),
            "error_message": item.get("error_message"),
        }
        for key, item in sorted(outcomes.items())
        if item.get("status") != "success"
    ]
    succeeded = sum(1 for item in outcomes.values() if item.get("status") == "success")
    return MergeResult(
        records=records,
        entries_succeeded=succeeded,
        entries_failed=len(failed),
        failed_entries=failed,
        run_dirs=run_dirs,
    )


def write_merge_outputs(result: MergeResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in result.records),
        encoding="utf-8",
    )
    stats = compute_stats(result.records)
    stats["entries_succeeded"] = result.entries_succeeded
    stats["entries_failed"] = result.entries_failed
    stats["runs"] = [str(path.parent.name) for path in result.run_dirs]
    (out_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "failures.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in result.failed_entries),
        encoding="utf-8",
    )
    return records_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=repo_root() / "packages/data_ingestion/tmp/pharmacopoeia-ingestion",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=repo_root()
        / "datasets/baicao-knowledge/sources/national-standard-2022-pharmacopoeia/processed/latest",
    )
    args = parser.parse_args()
    result = merge_runs(args.runs_root)
    write_merge_outputs(result, args.out_dir)
    print(
        json.dumps(
            {
                "runs": len(result.run_dirs),
                "records": len(result.records),
                "entries_succeeded": result.entries_succeeded,
                "entries_failed": result.entries_failed,
                "out": str(args.out_dir),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
