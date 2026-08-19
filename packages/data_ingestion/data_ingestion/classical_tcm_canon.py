"""只读审计 classical-tcm-canon：书目统计，不把全文写入图谱。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "classical-tcm-canon"
IMPORT_SCOPE_KEY = "huggingface:wangekxy/classical-tcm-canon"
DEFAULT_BATCH_ID = "2026-08-19-classical-tcm-canon-v1"
PROCESSOR = "classical_tcm_canon"
PROMPT_HASH = prompt_hash_for(Path(__file__))
REQUIRED_COLUMNS = (
    "id",
    "work_family",
    "title",
    "char_count",
    "text",
)


class ClassicalTcmCanonError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root() / ".cache/huggingface/wangekxy/classical-tcm-canon/classical-tcm-canon.parquet"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_parquet(path: Path) -> dict[str, list[Any]]:
    try:
        parquet = __import__("pyarrow.parquet", fromlist=["read_table"])
    except ImportError as exc:
        raise ClassicalTcmCanonError("pyarrow is required to read classical-tcm-canon") from exc
    table = parquet.read_table(path)
    return {name: table.column(name).to_pylist() for name in table.column_names}


def clean_file(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_file():
        raise ClassicalTcmCanonError(f"missing parquet: {path}")
    columns = _read_parquet(path)
    missing = [name for name in REQUIRED_COLUMNS if name not in columns]
    if missing:
        raise ClassicalTcmCanonError(f"missing columns: {missing}")
    row_count = len(columns["id"])
    if row_count == 0:
        raise ClassicalTcmCanonError("parquet is empty")
    ids = [str(value) for value in columns["id"]]
    titles = [str(value).strip() for value in columns["title"]]
    if len(set(ids)) != row_count:
        raise ClassicalTcmCanonError("duplicate work id")
    if len(set(titles)) != row_count:
        raise ClassicalTcmCanonError("duplicate title")
    empty_text = 0
    char_sum = 0
    for index, text in enumerate(columns["text"]):
        body = str(text or "")
        if not body.strip():
            empty_text += 1
        char_sum += int(columns["char_count"][index] or 0)
    if empty_text:
        raise ClassicalTcmCanonError(f"empty text rows: {empty_text}")

    families = Counter(str(value) for value in columns.get("work_family", []))
    ship = Counter(str(value) for value in columns.get("ship_tier", []))
    records: list[DatasetRecord] = []
    report = {
        "publish": False,
        "license_status": "other_proprietary_commercial_pd_claim",
        "consumed_files": [path.name],
        "file_sha256": {path.name: _sha256(path)},
        "work_count": row_count,
        "char_count_sum": char_sum,
        "work_family_counts": dict(sorted(families.items())),
        "ship_tier_counts": dict(sorted(ship.items())),
        "mapped_relation_counts": {},
        "quarantine_counts": {"full_text_works": row_count},
        "quality_samples": {
            "first_title": titles[0],
            "last_title": titles[-1],
        },
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
    }
    return records, report


def write_clean_outputs(
    records: list[DatasetRecord], report: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    if records:
        raise ClassicalTcmCanonError("classical-tcm-canon must not emit graph records")
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text("", encoding="utf-8")
    stats = {**compute_stats(records), **report}
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": 0,
        "edge_count": 0,
        "publish": False,
    }
